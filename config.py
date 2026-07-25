import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # ── MySQL Configuration (for production) ──
    # Uncomment below and set your MySQL password to use MySQL:
    # MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    # MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'yourpassword')
    # MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    # MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    # MYSQL_DB = os.environ.get('MYSQL_DB', 'study_planner')
    # SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'

    # ── SQLite Configuration (for local development) ──
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "study_planner.db")}'
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
