import csv
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CSV_USERS

def upsert_user_to_csv(email: str, role: str):
    CSV_USERS.parent.mkdir(parents=True, exist_ok=True)
    rows  = []
    found = False
    if CSV_USERS.exists():
        with open(CSV_USERS, "r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["email"] == email:
                    row["role"] = role
                    row["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    found = True
                rows.append(row)
    if not found:
        rows.append({"email": email, "role": role,
                     "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "updated_at": ""})
    with open(CSV_USERS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email","role","created_at","updated_at"])
        writer.writeheader()
        writer.writerows(rows)