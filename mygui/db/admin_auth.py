import sqlite3
from db.db_paths import ADMIN_DB_PATH


def init_admin_auth_db():
    """Initialize admin authentication database in the specified directory."""
    
    conn = sqlite3.connect(str(ADMIN_DB_PATH))
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_name TEXT,
            designation TEXT,
            password TEXT,
            PRIMARY KEY (admin_name, designation)
        )
    """)

    # Default designation passwords
    defaults = [
        ("_default", "Senior Test Engineer", "admin10"),
        ("_default", "Manager", "admin11"),
        ("_default", "General Manager", "admin12"),
    ]

    for admin_name, designation, password in defaults:
        cur.execute(
            "INSERT OR IGNORE INTO admins (admin_name, designation, password) VALUES (?, ?, ?)",
            (admin_name, designation, password)
        )

    conn.commit()
    conn.close()