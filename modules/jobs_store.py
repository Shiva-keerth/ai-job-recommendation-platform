import sqlite3
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


def init_jobs_table():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        job_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employer_email TEXT, job_title TEXT, category TEXT, industry TEXT,
        skills TEXT, location TEXT, work_mode TEXT, experience_level TEXT,
        salary_range TEXT, job_description TEXT, status TEXT DEFAULT 'open', created_at TEXT
    )""")
    conn.commit(); conn.close()


def save_job(employer_email, job_data):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
    INSERT INTO jobs(employer_email,job_title,category,industry,skills,location,
        work_mode,experience_level,salary_range,job_description,status,created_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    """, (employer_email, job_data.get("job_title",""), job_data.get("category",""),
          job_data.get("industry",""), job_data.get("skills",""), job_data.get("location",""),
          job_data.get("work_mode",""), job_data.get("experience_level",""),
          job_data.get("salary_range",""), job_data.get("description",""),
          "open", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit(); conn.close()
    return True, "✅ Job posted successfully!"


def get_employer_jobs(employer_email):
    conn = sqlite3.connect(str(DB_PATH))
    cur  = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE employer_email=? ORDER BY created_at DESC", (employer_email,))
    rows = cur.fetchall(); conn.close()
    return rows


def get_open_jobs():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute("""
        SELECT job_id,employer_email,job_title,category,industry,skills,
               location,work_mode,experience_level,salary_range,job_description,status,created_at
        FROM jobs WHERE status='open' ORDER BY created_at DESC
    """)
    rows = cur.fetchall(); conn.close()
    return rows