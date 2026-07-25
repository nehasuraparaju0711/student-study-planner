"""
Student Study Planner — Flask Application
==========================================
Main application file with all routes for authentication, subject/task CRUD,
availability management, schedule generation, and analytics.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
from config import Config
from models import db, User, Subject, Task, StudySlot, ScheduleEntry
from scheduler import generate_schedule, compute_stats


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Auth Routes ───────────────────────────────────────────────────────

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm = request.form.get('confirm_password', '')

            if not username or not email or not password:
                flash('All fields are required.', 'error')
                return redirect(url_for('register'))
            if password != confirm:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('register'))
            if User.query.filter_by(username=username).first():
                flash('Username already taken.', 'error')
                return redirect(url_for('register'))
            if User.query.filter_by(email=email).first():
                flash('Email already registered.', 'error')
                return redirect(url_for('register'))

            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            login_user(user)
            flash('Account created successfully!', 'success')
            return redirect(url_for('dashboard'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out successfully.', 'success')
        return redirect(url_for('login'))

    # ── Dashboard ─────────────────────────────────────────────────────────

    @app.route('/dashboard')
    @login_required
    def dashboard():
        subjects = Subject.query.filter_by(user_id=current_user.id).all()
        tasks = Task.query.filter_by(user_id=current_user.id).all()
        entries = ScheduleEntry.query.filter_by(user_id=current_user.id).all()
        stats = compute_stats(tasks, entries, subjects)
        return render_template('dashboard.html', stats=stats, subjects=subjects)

    # ── Subjects CRUD ─────────────────────────────────────────────────────

    @app.route('/subjects', methods=['GET', 'POST'])
    @login_required
    def subjects():
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            priority = request.form.get('priority', 'medium')
            difficulty = request.form.get('difficulty', 'medium')
            weekly_hours = float(request.form.get('weekly_target_hours', 5))
            color = request.form.get('color', '#6C63FF')

            if not name:
                flash('Subject name is required.', 'error')
                return redirect(url_for('subjects'))

            subject = Subject(
                user_id=current_user.id,
                name=name,
                priority=priority,
                difficulty=difficulty,
                weekly_target_hours=weekly_hours,
                color=color
            )
            db.session.add(subject)
            db.session.commit()
            flash(f'Subject "{name}" added!', 'success')
            return redirect(url_for('subjects'))

        all_subjects = Subject.query.filter_by(user_id=current_user.id).all()
        return render_template('subjects.html', subjects=all_subjects)

    @app.route('/api/subjects/<int:sid>', methods=['DELETE'])
    @login_required
    def delete_subject(sid):
        subj = Subject.query.filter_by(id=sid, user_id=current_user.id).first_or_404()
        db.session.delete(subj)
        db.session.commit()
        return jsonify({'status': 'deleted'})

    # ── Tasks CRUD ────────────────────────────────────────────────────────

    @app.route('/tasks', methods=['GET', 'POST'])
    @login_required
    def tasks():
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            subject_id = int(request.form.get('subject_id', 0))
            description = request.form.get('description', '').strip()
            deadline_str = request.form.get('deadline', '')
            estimated_hours = float(request.form.get('estimated_hours', 1))

            if not title or not subject_id or not deadline_str:
                flash('Title, subject, and deadline are required.', 'error')
                return redirect(url_for('tasks'))

            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')

            task = Task(
                user_id=current_user.id,
                subject_id=subject_id,
                title=title,
                description=description,
                deadline=deadline,
                estimated_hours=estimated_hours
            )
            db.session.add(task)
            db.session.commit()
            flash(f'Task "{title}" added!', 'success')
            return redirect(url_for('tasks'))

        all_tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.deadline.asc()).all()
        all_subjects = Subject.query.filter_by(user_id=current_user.id).all()
        return render_template('subjects.html', tasks=all_tasks, subjects=all_subjects, show_tasks=True)

    @app.route('/api/tasks/<int:tid>/complete', methods=['PUT'])
    @login_required
    def complete_task(tid):
        task = Task.query.filter_by(id=tid, user_id=current_user.id).first_or_404()
        task.completed = not task.completed
        task.completed_at = datetime.utcnow() if task.completed else None
        db.session.commit()
        return jsonify({'status': 'toggled', 'completed': task.completed})

    @app.route('/api/tasks/<int:tid>', methods=['DELETE'])
    @login_required
    def delete_task(tid):
        task = Task.query.filter_by(id=tid, user_id=current_user.id).first_or_404()
        db.session.delete(task)
        db.session.commit()
        return jsonify({'status': 'deleted'})

    # ── Availability ──────────────────────────────────────────────────────

    @app.route('/availability', methods=['GET', 'POST'])
    @login_required
    def availability():
        if request.method == 'POST':
            # Clear existing slots
            StudySlot.query.filter_by(user_id=current_user.id).delete()

            data = request.get_json()
            for slot in data.get('slots', []):
                s = StudySlot(
                    user_id=current_user.id,
                    day_of_week=int(slot['day']),
                    start_hour=int(slot['start']),
                    end_hour=int(slot['end'])
                )
                db.session.add(s)
            db.session.commit()
            return jsonify({'status': 'saved'})

        slots = StudySlot.query.filter_by(user_id=current_user.id).all()
        slots_data = [{'day': s.day_of_week, 'start': s.start_hour, 'end': s.end_hour} for s in slots]
        return render_template('schedule.html', slots=slots_data, show_availability=True)

    # ── Schedule Generation ───────────────────────────────────────────────

    @app.route('/api/generate-schedule', methods=['POST'])
    @login_required
    def gen_schedule():
        subjects = Subject.query.filter_by(user_id=current_user.id).all()
        tasks_list = Task.query.filter_by(user_id=current_user.id, completed=False).all()
        slots = StudySlot.query.filter_by(user_id=current_user.id).all()

        if not subjects:
            return jsonify({'error': 'Add at least one subject first.'}), 400
        if not slots:
            return jsonify({'error': 'Set your availability first.'}), 400

        # Clear old schedule for current week
        week_start = date.today() - timedelta(days=date.today().weekday())
        ScheduleEntry.query.filter_by(
            user_id=current_user.id, week_start_date=week_start
        ).delete()

        entries = generate_schedule(subjects, tasks_list, slots, current_user.id)

        for e in entries:
            db.session.add(ScheduleEntry(**e))
        db.session.commit()

        return jsonify({'status': 'generated', 'count': len(entries)})

    @app.route('/schedule')
    @login_required
    def schedule():
        week_start = date.today() - timedelta(days=date.today().weekday())
        entries = ScheduleEntry.query.filter_by(
            user_id=current_user.id, week_start_date=week_start
        ).order_by(ScheduleEntry.day_of_week, ScheduleEntry.start_hour).all()

        subjects = Subject.query.filter_by(user_id=current_user.id).all()
        subject_map = {s.id: s for s in subjects}
        slots = StudySlot.query.filter_by(user_id=current_user.id).all()
        slots_data = [{'day': s.day_of_week, 'start': s.start_hour, 'end': s.end_hour} for s in slots]

        return render_template('schedule.html', entries=entries, subject_map=subject_map,
                               slots=slots_data, week_start=week_start.strftime('%Y-%m-%d'))

    # ── Stats API ─────────────────────────────────────────────────────────

    @app.route('/api/stats')
    @login_required
    def stats_api():
        subjects = Subject.query.filter_by(user_id=current_user.id).all()
        tasks_list = Task.query.filter_by(user_id=current_user.id).all()
        entries = ScheduleEntry.query.filter_by(user_id=current_user.id).all()
        return jsonify(compute_stats(tasks_list, entries, subjects))

    return app


# ── Entry Point ───────────────────────────────────────────────────────────

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
