from passlib.hash import pbkdf2_sha256
from modules.db import get_conn
from modules.csv_store import upsert_user_to_csv


def verify_login(email, password):
    email = email.strip().lower()
    password = password.strip()
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT password_hash, role FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False, None
    password_hash, role = row
    return pbkdf2_sha256.verify(password, password_hash), role


def register_user(email, password, role="candidate"):
    email = email.strip().lower()
    conn = get_conn()
    cur  = conn.cursor()
    if "@" not in email:
        conn.close()
        return False, "Please enter a valid email."
    if len(password) < 6:
        conn.close()
        return False, "Password must be at least 6 characters."
    cur.execute("SELECT email FROM users WHERE email=?", (email,))
    if cur.fetchone():
        conn.close()
        return False, "Email already registered. Please login."
    password_hash = pbkdf2_sha256.hash(password)
    cur.execute("INSERT INTO users(email,password_hash,role) VALUES(?,?,?)",
                (email, password_hash, role))
    conn.commit()
    conn.close()
    upsert_user_to_csv(email, role)
    return True, "Registration successful! Now login."


def create_admin_if_missing(email: str, password: str):
    email = email.strip().lower()
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT email FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    password_hash = pbkdf2_sha256.hash(password)
    if not row:
        cur.execute("INSERT INTO users(email,password_hash,role) VALUES(?,?,?)",
                    (email, password_hash, "admin"))
        conn.commit()
        upsert_user_to_csv(email, "admin")
    else:
        # Always update password hash to ensure correct credentials
        cur.execute("UPDATE users SET password_hash=?, role=? WHERE email=?",
                    (password_hash, "admin", email))
        conn.commit()
    conn.close()


def get_all_users():
    """Admin: returns all users (id, email, role)."""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT id, email, role FROM users ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_user(user_id: int):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def update_user_role(user_id: int, new_role: str):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
    conn.commit()
    conn.close()