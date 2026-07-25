from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User account model for authentication and session management."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    subjects = db.relationship('Subject', backref='user', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')
    study_slots = db.relationship('StudySlot', backref='user', lazy=True, cascade='all, delete-orphan')
    schedule_entries = db.relationship('ScheduleEntry', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Subject(db.Model):
    """Academic subject with priority and difficulty metadata."""
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.String(10), default='medium')    # high, medium, low
    difficulty = db.Column(db.String(10), default='medium')  # hard, medium, easy
    weekly_target_hours = db.Column(db.Float, default=5.0)
    color = db.Column(db.String(7), default='#6C63FF')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    tasks = db.relationship('Task', backref='subject', lazy=True, cascade='all, delete-orphan')
    schedule_entries = db.relationship('ScheduleEntry', backref='subject', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Subject {self.name}>'


class Task(db.Model):
    """Individual study task linked to a subject with deadline tracking."""
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=False)
    estimated_hours = db.Column(db.Float, default=1.0)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Task {self.title}>'


class StudySlot(db.Model):
    """User's weekly availability time slot."""
    __tablename__ = 'study_slots'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_hour = db.Column(db.Integer, nullable=False)    # 0-23
    end_hour = db.Column(db.Integer, nullable=False)      # 0-23
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StudySlot Day:{self.day_of_week} {self.start_hour}:00-{self.end_hour}:00>'


class ScheduleEntry(db.Model):
    """Generated schedule entry — a single study block in the weekly plan."""
    __tablename__ = 'schedule_entries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    day_of_week = db.Column(db.Integer, nullable=False)   # 0=Monday, 6=Sunday
    start_hour = db.Column(db.Integer, nullable=False)     # 0-23
    duration_hours = db.Column(db.Float, default=1.0)
    week_start_date = db.Column(db.Date, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to task
    task = db.relationship('Task', backref='schedule_entries', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject_id': self.subject_id,
            'task_id': self.task_id,
            'day_of_week': self.day_of_week,
            'start_hour': self.start_hour,
            'duration_hours': self.duration_hours,
            'week_start_date': self.week_start_date.strftime('%Y-%m-%d') if self.week_start_date else None,
            'is_completed': self.is_completed
        }

    def __repr__(self):
        return f'<ScheduleEntry Day:{self.day_of_week} {self.start_hour}:00 ({self.duration_hours}h)>'

