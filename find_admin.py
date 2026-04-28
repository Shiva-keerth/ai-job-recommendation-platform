from modules.db import get_conn

conn = get_conn()
cur = conn.cursor()

cur.execute("SELECT email, role FROM users")
rows = cur.fetchall()

print("---- ADMIN ACCOUNTS ----")
found = False

for email, role in rows:
    if str(role).strip().lower() == "admin":
        print("ADMIN:", email)
        found = True

if not found:
    print("No admin user found in DB.")

conn.close()