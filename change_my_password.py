import sqlite3
import getpass
from passlib.hash import pbkdf2_sha256
from pathlib import Path

def change_password():
    db_path = Path(__file__).parent / "db" / "app.db"
    
    print("\n--- 🔐 UPDATE ACCOUNT PASSWORD ---")
    email = input("Enter your account email: ").strip().lower()
    
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    
    if not user:
        print("❌ Error: Email not found in the database. Are you sure you registered?")
        conn.close()
        return

    new_password = getpass.getpass("Enter your new preferred password (it will be hidden): ").strip()
    
    if len(new_password) < 6:
        print("❌ Error: Password must be at least 6 characters.")
        conn.close()
        return
        
    phash = pbkdf2_sha256.hash(new_password)
    cur.execute("UPDATE users SET password_hash=? WHERE email=?", (phash, email))
    conn.commit()
    conn.close()
    
    print(f"\n✅ Success! Your password has been updated.")
    print("You can now refresh the app and log in substituting your custom password.\n")

if __name__ == "__main__":
    change_password()
