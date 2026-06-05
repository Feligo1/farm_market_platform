# test_login.py
import psycopg2
from werkzeug.security import check_password_hash

conn = psycopg2.connect(
    host="ep-bitter-cell-alftjnnc-pooler.c-3.eu-central-1.aws.neon.tech",
    port=5432,
    database="neondb",
    user="neondb_owner",
    password="npg_MEfFwbeRV57O",
    sslmode="require"
)
cursor = conn.cursor()

cursor.execute("SELECT username, password_hash FROM users WHERE username = 'Felix'")
user = cursor.fetchone()

if user:
    username, stored_hash = user
    password_to_test = '5645'
    
    result = check_password_hash(stored_hash, password_to_test)
    print(f"Username: {username}")
    print(f"Password to test: {password_to_test}")
    print(f"Password match: {result}")
    
    if result:
        print("✅ Login would succeed!")
    else:
        print("❌ Login would fail - hash mismatch")
else:
    print("User not found")

cursor.close()
conn.close()