# 📚 Student Study Planner

A full-stack web application built with **Python Flask, HTML, CSS, JavaScript, and MySQL** that processes user-input data (subjects, deadlines, available hours) to auto-generate a personalized weekly study schedule using rule-based logic.

## Features

- **User Authentication** — Signup/login with secure password hashing
- **Subject Management** — Add subjects with priority, difficulty, weekly target hours, and color coding
- **Task Tracking** — Create tasks with deadlines and estimated hours; mark as complete
- **Availability Grid** — Interactive drag-to-select weekly availability calendar
- **Auto-Scheduling** — Rule-based engine generates optimized weekly study schedules using composite scoring:
  - Deadline urgency scoring
  - Priority weighting (High: 3x, Medium: 2x, Low: 1x)
  - Difficulty-based block sizing
  - Spaced repetition across days
  - Balance cap (no subject > 40% of weekly hours)
- **Analytics Dashboard** — Completion rate, study hours breakdown, deadline adherence, upcoming deadlines
- **Persistent Data** — MySQL database stores user data across sessions for pattern tracking

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, Flask, Flask-SQLAlchemy, Flask-Login |
| Frontend | HTML5, CSS3 (vanilla), JavaScript (vanilla) |
| Database | MySQL (via PyMySQL) |

## Setup

### Prerequisites
- Python 3.8+
- MySQL Server

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/nehasuraparaju0711/student-study-planner.git
   cd student-study-planner
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create the MySQL database**
   ```sql
   CREATE DATABASE study_planner;
   ```

5. **Configure environment variables** (optional)
   ```bash
   export MYSQL_USER=root
   export MYSQL_PASSWORD=yourpassword
   export MYSQL_HOST=localhost
   export MYSQL_PORT=3306
   export MYSQL_DB=study_planner
   ```
   Or edit `config.py` directly.

6. **Initialize database tables**
   ```bash
   python init_db.py
   ```

7. **Run the application**
   ```bash
   python app.py
   ```

8. Open **http://localhost:5000** in your browser.

## Database Schema

```
Users ─┬── Subjects ─┬── Tasks
       │             └── ScheduleEntries
       ├── StudySlots
       └── ScheduleEntries
```

- **Users** — Authentication and session management
- **Subjects** — Academic subjects with priority/difficulty metadata
- **Tasks** — Study tasks with deadlines and estimated hours
- **StudySlots** — Weekly availability time slots
- **ScheduleEntries** — Generated schedule blocks

## Scheduling Algorithm

The rule-based engine uses a **composite score** to rank and allocate tasks:

```
Score = urgency × priority_weight × (1 + difficulty_factor)
```

Where:
- `urgency = 1 / days_until_deadline`
- `priority_weight` = High: 3, Medium: 2, Low: 1
- `difficulty_factor` = Hard: 0.5, Medium: 0.25, Easy: 0

Tasks are sorted by score and greedily allocated to available time slots with spaced repetition across days.

## License

MIT
