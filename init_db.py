"""
Database initialization script.
Creates the MySQL database and all tables.

Usage:
    python init_db.py
"""

from app import create_app
from models import db


def init_database():
    app = create_app()
    with app.app_context():
        # Create all tables defined in models.py
        db.create_all()
        print("✅ Database tables created successfully!")
        print("   Tables: users, subjects, tasks, study_slots, schedule_entries")


if __name__ == '__main__':
    init_database()
