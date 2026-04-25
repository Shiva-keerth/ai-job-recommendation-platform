from datetime import datetime
from modules.db import get_conn


def ensure_feedback_columns():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT, job_id TEXT, job_title TEXT, company TEXT,
        score REAL, status TEXT, applied_at TEXT
    )""")
    cur.execute("PRAGMA table_info(applications)")
    cols = {row[1] for row in cur.fetchall()}
    for col, typ in [
        ("rating","INTEGER"), ("comment","TEXT"), ("updated_at","TEXT"),
        ("job_source","TEXT"), ("employer_email","TEXT"),
        ("resume_skills","TEXT"), ("resume_category","TEXT"),
    ]:
        if col not in cols:
            cur.execute(f"ALTER TABLE applications ADD COLUMN {col} {typ}")
    conn.commit()
    conn.close()


def save_application(user_email, job_id, job_title, company, score,
                     job_source="csv", employer_email="",
                     resume_skills=None, resume_category=""):
    ensure_feedback_columns()
    if resume_skills is None:
        rs = ""
    elif isinstance(resume_skills, (list, set, tuple)):
        rs = ", ".join([str(x).strip().lower() for x in resume_skills if str(x).strip()])
    else:
        rs = str(resume_skills)

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT id FROM applications WHERE user_email=? AND job_id=?", (user_email, str(job_id)))
    if cur.fetchone():
        conn.close()
        return False, "You already applied to this job."

    cur.execute("""
        INSERT INTO applications(user_email,job_id,job_title,company,score,status,applied_at,
            job_source,employer_email,resume_skills,resume_category)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (user_email, str(job_id), job_title, company, float(score), "Applied",
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          job_source, employer_email, rs, str(resume_category or "")))
    conn.commit()
    conn.close()

    # log activity
    _log("application_submitted", user_email, f"Applied to {job_title} at {company}")
    return True, "Application submitted successfully ✅"


def get_user_applications(user_email):
    ensure_feedback_columns()
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT job_id, job_title, company, score, status, applied_at,
               COALESCE(rating,''), COALESCE(comment,''), COALESCE(updated_at,'')
        FROM applications WHERE user_email=? ORDER BY applied_at DESC
    """, (user_email,))
    rows = cur.fetchall()
    conn.close()
    return rows


def update_application_status(app_id, status, rating=None, comment=""):
    ensure_feedback_columns()
    conn = get_conn()
    cur  = conn.cursor()

    # ── Fetch application details BEFORE updating (for email) ────────
    cur.execute("""
        SELECT user_email, job_title, company
        FROM applications WHERE id=?
    """, (int(app_id),))
    app_row = cur.fetchone()

    cur.execute("""
        UPDATE applications SET status=?,rating=?,comment=?,updated_at=? WHERE id=?
    """, (status, rating, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), int(app_id)))
    conn.commit()
    changed = cur.rowcount
    conn.close()

    if changed == 0:
        return False, "❌ Application not found."

    # ── Send email notification for key status changes ────────────────
    if app_row and status in ("Shortlisted", "Interview", "Selected", "Rejected"):
        try:
            from modules.otp_service import send_status_notification
            candidate_email = app_row[0]
            job_title       = app_row[1]
            company         = app_row[2]
            candidate_name  = candidate_email.split("@")[0].replace(".", " ").title()
            send_status_notification(
                candidate_email = candidate_email,
                candidate_name  = candidate_name,
                job_title       = job_title,
                company         = company,
                new_status      = status,
                employer_comment= str(comment or ""),
            )
        except Exception:
            pass  # never block status update if email fails

    return True, "✅ Status / feedback updated."


def get_employer_applications(employer_email):
    ensure_feedback_columns()
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, user_email, job_id, job_title, company, score, status, applied_at,
               COALESCE(rating,''), COALESCE(comment,''), COALESCE(updated_at,''),
               COALESCE(job_source,''), COALESCE(employer_email,'')
        FROM applications WHERE employer_email=? ORDER BY applied_at DESC
    """, (employer_email,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_applications_for_job(employer_email, job_id):
    ensure_feedback_columns()
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, user_email, job_id, job_title, company, score, status, applied_at,
               COALESCE(rating,''), COALESCE(comment,''), COALESCE(updated_at,''),
               COALESCE(resume_skills,''), COALESCE(resume_category,'')
        FROM applications WHERE employer_email=? AND job_id=?
        ORDER BY score DESC, applied_at DESC
    """, (employer_email, str(job_id)))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_applications():
    """Admin: all applications across the system."""
    ensure_feedback_columns()
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, user_email, job_id, job_title, company, score, status, applied_at,
               COALESCE(job_source,''), COALESCE(employer_email,'')
        FROM applications ORDER BY applied_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def _log(event_type, actor_email, detail):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO activity_log(event_type,actor_email,detail,created_at)
            VALUES(?,?,?,?)
        """, (event_type, actor_email, detail, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception:
        pass