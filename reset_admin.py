from passlib.hash import pbkdf2_sha256
from modules.db import get_conn

ADMIN_EMAIL = "admin@project.com"

print("Resetting password for:", ADMIN_EMAIL)
new_password = input("Enter NEW password: ").strip()

if len(new_password) < 6:
    print("❌ Password must be at least 6 characters.")
    raise SystemExit

conn = get_conn()
cur = conn.cursor()

# confirm user exists
cur.execute("SELECT email, role, password_hash FROM users WHERE email=?", (ADMIN_EMAIL,))
row = cur.fetchone()

if not row:
    print("❌ Admin not found in users table.")
    conn.close()
    raise SystemExit

email, role, old_hash = row
print("Found:", email, "| role:", role)
print("Old hash starts with:", old_hash[:20])

# update hash
new_hash = pbkdf2_sha256.hash(new_password)
cur.execute("UPDATE users SET password_hash=? WHERE email=?", (new_hash, ADMIN_EMAIL))
conn.commit()

print("Rows updated:", cur.rowcount)

# verify immediately
cur.execute("SELECT password_hash FROM users WHERE email=?", (ADMIN_EMAIL,))
saved_hash = cur.fetchone()[0]

print("New hash starts with:", saved_hash[:20])
print("Verify test:", pbkdf2_sha256.verify(new_password, saved_hash))

conn.close()
print("✅ Done. Now login with the new password you typed.")
