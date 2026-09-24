# 📚 Student Study Planner

A full-stack, intelligent study planner web application built with **Python Flask**, **SQLite / MySQL**, and modern **Glassmorphism CSS/JS UI**. It processes student subjects, task deadlines, and available time slots to automatically generate an optimized, personalized weekly study schedule using a composite scoring algorithm.

---

## 🌟 Highlights & Features

- 🔐 **User Authentication** — Secure user signup and login system using Flask-Login and password hashing via Werkzeug (`pbkdf2:sha256`).
- 📚 **Subject Management** — Organize subjects with customizable target weekly hours, difficulty level (*Hard*, *Medium*, *Easy*), priority weighting (*High*, *Medium*, *Low*), and vibrant hex color codes.
- 📝 **Task Tracking with Deadlines** — Add study tasks linked to specific subjects with estimated effort hours and strict completion deadlines.
- 📅 **Interactive Availability Grid** — Intuitive, drag-to-select weekly calendar grid (Monday–Sunday, 6 AM–11 PM) to set free study windows.
- ⚡ **Smart Auto-Scheduler Engine** — Composite scoring rule engine that balances workload across available slots considering:
  - **Deadline Urgency** ($1 / \text{days remaining}$)
  - **Priority Weighting** (High: 3.0×, Medium: 2.0×, Low: 1.0×)
  - **Difficulty Block Sizing** (Hard: +50% allocation boost)
  - **Spaced Repetition** (distributes study sessions across days to avoid cramming)
  - **Balance Cap** (prevents any single subject from exceeding 40% of weekly capacity)
- 📊 **Analytics & Visualizations** — Visual breakdown of completion status, subject study hour distribution, deadline adherence rate, and interactive canvas charts.
- 💎 **Lumina Glassmorphic Dark UI** — Modern, aesthetic dark-mode user interface featuring translucent glass cards, fluid gradient accents, and responsive layout.
- 🗄️ **Dual Database Support** — Zero-config **SQLite** out-of-the-box for instant local execution, plus **MySQL** support for scalable production deployments.

---

## 🏗️ Project Architecture & File Structure

```
student-study-planner/
├── app.py              # Main Flask application with Web & REST API routes
├── config.py           # Configuration settings (SQLite local / MySQL production)
├── models.py           # SQLAlchemy ORM models (User, Subject, Task, StudySlot, ScheduleEntry)
├── scheduler.py        # Rule-based auto-scheduling algorithm engine
├── init_db.py          # Database initialization script
├── requirements.txt    # Python dependencies
├── study_planner.db    # Local SQLite database instance (auto-generated)
├── static/
│   ├── css/
│   │   └── style.css   # Lumina glassmorphic theme styling & CSS variables
│   └── js/
│       └── main.js     # Availability grid drag handler, charts, dynamic filters
└── templates/
    ├── base.html       # Master layout with navigation bar & flash messages
    ├── index.html      # Public landing page
    ├── login.html      # Login authentication view
    ├── register.html   # User registration view
    ├── dashboard.html  # Main overview dashboard
    ├── subjects.html   # Subject creation & management
    ├── tasks.html      # Task tracking & management
    ├── availability.html # Weekly availability grid configuration
    ├── schedule.html   # Generated weekly study plan calendar view
    └── analytics.html  # Progress analytics & visualization charts
```

---

## 🗄️ Database Schema

The database consists of 5 relational entities:

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    Users    │──────<│  Subjects   │──────<│    Tasks    │
└──────┬──────┘       └──────┬──────┘       └──────┬──────┘
       │                     │                     │
       │                     └──────────┬──────────┘
       │                                │
       ├───────────────────────────────>│
       │                         ┌──────┴──────────────┐
       └────────────────────────>│   ScheduleEntries   │
                                 └─────────────────────┘
```

1. **`Users`**: User account credentials, hashed password, email, and metadata.
2. **`Subjects`**: User's subjects with priority, difficulty, color code, and weekly target hours.
3. **`Tasks`**: Specific assignments, exam prep, or readings with deadlines and estimated hours.
4. **`StudySlots`**: Recurring weekly available time slots (Day of week 0–6, start hour, end hour).
5. **`ScheduleEntries`**: Output generated study blocks assigned to specific subjects, tasks, and time slots.

---

## 🧠 Smart Scheduling Algorithm

The rule-based algorithm in [`scheduler.py`](file:///Users/rohitverma/.gemini/antigravity-ide/scratch/study-planner/scheduler.py) ranks unassigned tasks and subject targets using a composite priority score:

$$\text{Composite Score} = \text{Urgency} \times \text{Priority Weight} \times (1 + \text{Difficulty Factor})$$

- **Urgency Factor**: $\frac{1}{\max(1, \text{days until deadline})}$
- **Priority Weight**: High = $3.0$, Medium = $2.0$, Low = $1.0$
- **Difficulty Factor**: Hard = $0.50$, Medium = $0.25$, Easy = $0.00$

Allocations are greedily scheduled into available user study slots while enforcing spaced repetition limits (max study hours per day per subject) and weekly balance constraints.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.8+** installed on your system.
- *(Optional)* MySQL Server if running in production mode.

### Quick Setup (SQLite Local Dev)

1. **Clone the repository**
   ```bash
   git clone https://github.com/nehasuraparaju0711/student-study-planner.git
   cd student-study-planner
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate    # On Windows: venv\Scripts\activate
   ```

3. **Install required dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. Open **http://localhost:5000** in your web browser.

---

## ⚙️ Configuration & MySQL Deployment

By default, the app uses an auto-created SQLite database file (`study_planner.db`).

To switch to **MySQL**:
1. Configure environment variables in your terminal:
   ```bash
   export MYSQL_USER=root
   export MYSQL_PASSWORD=your_password
   export MYSQL_HOST=localhost
   export MYSQL_PORT=3306
   export MYSQL_DB=study_planner
   ```
2. Or update the URI in [`config.py`](file:///Users/rohitverma/.gemini/antigravity-ide/scratch/study-planner/config.py):
   ```python
   SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@localhost:3306/study_planner'
   ```

---

## 🌐 API & Web Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Public landing page |
| `/login` | GET, POST | User authentication login |
| `/register` | GET, POST | New account registration |
| `/logout` | GET | User logout |
| `/dashboard` | GET | Overview dashboard with summary stats |
| `/subjects` | GET, POST | View and add subjects |
| `/subjects/delete/<id>` | POST | Delete subject |
| `/tasks` | GET, POST | View and create study tasks |
| `/tasks/toggle/<id>` | POST | Toggle task completion status |
| `/availability` | GET, POST | Manage weekly available study slots |
| `/schedule` | GET | View weekly auto-generated study schedule |
| `/schedule/generate` | POST | Trigger smart auto-scheduler engine |
| `/analytics` | GET | View study progress & performance analytics |

---

## 📄 License

This project is open-source under the **MIT License**.
