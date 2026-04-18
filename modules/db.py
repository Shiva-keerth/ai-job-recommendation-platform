import sqlite3
from pathlib import Path
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'candidate'
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        job_id TEXT,
        job_title TEXT,
        company TEXT,
        score REAL,
        status TEXT DEFAULT 'Applied',
        applied_at TEXT,
        rating INTEGER,
        comment TEXT,
        updated_at TEXT,
        job_source TEXT,
        employer_email TEXT,
        resume_skills TEXT,
        resume_category TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        job_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employer_email TEXT,
        job_title TEXT,
        category TEXT,
        industry TEXT,
        skills TEXT,
        location TEXT,
        work_mode TEXT,
        experience_level TEXT,
        salary_range TEXT,
        job_description TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS resume_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        resume_text TEXT,
        extracted_skills TEXT,
        detected_category TEXT,
        uploaded_at TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        actor_email TEXT,
        detail TEXT,
        created_at TEXT
    )""")

    # ── Migrate existing DB: rename description -> job_description if needed ──
    try:
        cur2 = conn.cursor()
        cur2.execute("PRAGMA table_info(jobs)")
        cols = [row[1] for row in cur2.fetchall()]
        if "description" in cols and "job_description" not in cols:
            cur2.execute("ALTER TABLE jobs RENAME COLUMN description TO job_description")
    except Exception:
        pass

    conn.commit()
    conn.close()