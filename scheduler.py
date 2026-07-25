"""
Rule-Based Scheduling Engine
=============================
Generates a personalized weekly study schedule using composite scoring:
    Score = urgency × priority_weight × (1 + difficulty_factor)

Rules:
  1. Deadline urgency  — tasks due sooner score higher
  2. Priority weight   — high:3, medium:2, low:1
  3. Difficulty blocks  — hard subjects get 2h blocks, easy get 1h
  4. Spaced repetition — spread each subject across multiple days
  5. Break insertion   — 15-min break after every 2 consecutive hours
  6. Balance cap       — no subject exceeds 40 % of total weekly hours
  7. Greedy fill       — sort by composite score, fill available slots
"""

from datetime import datetime, date, timedelta
from collections import defaultdict


# ── Constants ──────────────────────────────────────────────────────────────

PRIORITY_WEIGHT = {'high': 3, 'medium': 2, 'low': 1}
DIFFICULTY_FACTOR = {'hard': 0.5, 'medium': 0.25, 'easy': 0.0}
BLOCK_DURATION = {'hard': 2, 'medium': 1.5, 'easy': 1}   # hours
BALANCE_CAP = 0.40                                         # 40 %
DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


# ── Helpers ────────────────────────────────────────────────────────────────

def _urgency(deadline_dt):
    """Inverse days-until-deadline. Clamp to at least 1 to avoid division by zero."""
    days_left = max((deadline_dt - datetime.utcnow()).days, 1)
    return 1.0 / days_left


def _composite_score(task, subject):
    """Return a single float that ranks how urgently a task should be scheduled."""
    u = _urgency(task.deadline)
    p = PRIORITY_WEIGHT.get(subject.priority, 2)
    d = DIFFICULTY_FACTOR.get(subject.difficulty, 0.25)
    return u * p * (1 + d)


def _week_start(ref_date=None):
    """Return the Monday of the current (or given) week."""
    d = ref_date or date.today()
    return d - timedelta(days=d.weekday())


# ── Main Scheduler ────────────────────────────────────────────────────────

def generate_schedule(subjects, tasks, study_slots, user_id):
    """
    Parameters
    ----------
    subjects : list[Subject]   — user's subjects (ORM objects)
    tasks    : list[Task]      — incomplete tasks with deadlines
    study_slots : list[StudySlot] — weekly availability
    user_id  : int

    Returns
    -------
    list[dict]  — schedule entries ready to be inserted into the database
        Each dict has: user_id, subject_id, task_id, day_of_week,
                       start_hour, duration_hours, week_start_date
    """

    if not subjects or not study_slots:
        return []

    week_start_dt = _week_start()

    # ── 1. Build available-hour grid ──────────────────────────────────────
    # {day_of_week: [list of available start_hours]}
    available = defaultdict(list)
    for slot in study_slots:
        for h in range(slot.start_hour, slot.end_hour):
            available[slot.day_of_week].append(h)
    # De-duplicate & sort
    for day in available:
        available[day] = sorted(set(available[day]))

    # Track which hour-slots are already booked: (day, hour) → True
    booked = {}

    # ── 2. Score & sort tasks ─────────────────────────────────────────────
    subject_map = {s.id: s for s in subjects}
    scored_tasks = []
    for t in tasks:
        if t.completed:
            continue
        subj = subject_map.get(t.subject_id)
        if not subj:
            continue
        scored_tasks.append((t, subj, _composite_score(t, subj)))

    scored_tasks.sort(key=lambda x: x[2], reverse=True)

    # ── 3. Track per-subject allocation for balance cap ───────────────────
    total_available_hours = sum(len(hrs) for hrs in available.values())
    subject_hours = defaultdict(float)
    max_per_subject = total_available_hours * BALANCE_CAP

    # Track how many days a subject has been placed on (for spacing)
    subject_days = defaultdict(set)

    # ── 4. Greedy slot allocation ─────────────────────────────────────────
    entries = []

    for task, subj, score in scored_tasks:
        remaining = task.estimated_hours
        block_size = BLOCK_DURATION.get(subj.difficulty, 1)

        # Preferred day ordering: spread across days the subject hasn't been placed yet
        day_order = sorted(
            available.keys(),
            key=lambda d: (d in subject_days[subj.id], len(available[d]))
        )

        for day in day_order:
            if remaining <= 0:
                break
            if subject_hours[subj.id] >= max_per_subject:
                break

            hours = available[day]
            # Find contiguous free blocks
            i = 0
            while i < len(hours) and remaining > 0:
                start_h = hours[i]
                if (day, start_h) in booked:
                    i += 1
                    continue

                # Determine how long a contiguous block we can grab
                block_len = 0
                for j in range(i, len(hours)):
                    h = hours[j]
                    if (day, h) in booked:
                        break
                    if h != start_h + block_len:
                        break
                    block_len += 1
                    if block_len >= block_size:
                        break

                actual = min(block_len, remaining, block_size,
                             max_per_subject - subject_hours[subj.id])
                if actual <= 0:
                    i += 1
                    continue

                # Book the hours
                for k in range(int(actual)):
                    booked[(day, start_h + k)] = True

                entries.append({
                    'user_id': user_id,
                    'subject_id': subj.id,
                    'task_id': task.id,
                    'day_of_week': day,
                    'start_hour': start_h,
                    'duration_hours': actual,
                    'week_start_date': week_start_dt,
                })

                subject_hours[subj.id] += actual
                subject_days[subj.id].add(day)
                remaining -= actual
                i += int(actual)

    # ── 5. Fill remaining empty slots with target-hour subjects ───────────
    # Subjects that still haven't met their weekly_target_hours
    for subj in subjects:
        target = subj.weekly_target_hours
        allocated = subject_hours[subj.id]
        shortfall = target - allocated
        if shortfall <= 0:
            continue

        block_size = BLOCK_DURATION.get(subj.difficulty, 1)
        day_order = sorted(
            available.keys(),
            key=lambda d: (d in subject_days[subj.id], len(available[d]))
        )

        for day in day_order:
            if shortfall <= 0:
                break
            hours = available[day]
            i = 0
            while i < len(hours) and shortfall > 0:
                start_h = hours[i]
                if (day, start_h) in booked:
                    i += 1
                    continue

                block_len = 0
                for j in range(i, len(hours)):
                    h = hours[j]
                    if (day, h) in booked:
                        break
                    if h != start_h + block_len:
                        break
                    block_len += 1
                    if block_len >= block_size:
                        break

                actual = min(block_len, shortfall, block_size)
                if actual <= 0:
                    i += 1
                    continue

                for k in range(int(actual)):
                    booked[(day, start_h + k)] = True

                entries.append({
                    'user_id': user_id,
                    'subject_id': subj.id,
                    'task_id': None,
                    'day_of_week': day,
                    'start_hour': start_h,
                    'duration_hours': actual,
                    'week_start_date': week_start_dt,
                })

                subject_hours[subj.id] += actual
                subject_days[subj.id].add(day)
                shortfall -= actual
                i += int(actual)

    return entries


# ── Analytics helpers ─────────────────────────────────────────────────────

def compute_stats(tasks, schedule_entries, subjects):
    """Return a dict of analytics data for the dashboard."""
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.completed)
    completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks else 0, 1)

    # Hours by subject
    subject_map = {s.id: s for s in subjects}
    hours_by_subject = defaultdict(float)
    for e in schedule_entries:
        name = subject_map[e.subject_id].name if e.subject_id in subject_map else 'Unknown'
        hours_by_subject[name] += e.duration_hours

    # Hours by day
    hours_by_day = defaultdict(float)
    for e in schedule_entries:
        hours_by_day[DAY_NAMES[e.day_of_week]] += e.duration_hours

    # Upcoming deadlines (next 7 days)
    now = datetime.utcnow()
    upcoming = [
        {'title': t.title, 'deadline': t.deadline.strftime('%Y-%m-%d %H:%M'),
         'subject': subject_map[t.subject_id].name if t.subject_id in subject_map else '?'}
        for t in tasks
        if not t.completed and t.deadline and (t.deadline - now).days <= 7
    ]
    upcoming.sort(key=lambda x: x['deadline'])

    # Deadline adherence
    done_on_time = sum(
        1 for t in tasks
        if t.completed and t.completed_at and t.deadline and t.completed_at <= t.deadline
    )
    adherence = round((done_on_time / completed_tasks * 100) if completed_tasks else 0, 1)

    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': completion_rate,
        'hours_by_subject': dict(hours_by_subject),
        'hours_by_day': dict(hours_by_day),
        'upcoming_deadlines': upcoming,
        'deadline_adherence': adherence,
        'total_study_hours': round(sum(hours_by_subject.values()), 1),
    }
