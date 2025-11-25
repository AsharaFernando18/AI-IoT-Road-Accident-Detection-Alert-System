import sqlite3

conn = sqlite3.connect('database/database/roadsafenet.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"Tables: {', '.join(tables)}\n")

# Check Alert table
cursor.execute('PRAGMA table_info(Alert)')
print('Alert table columns:')
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

print()

# Check Incident table
cursor.execute('PRAGMA table_info(Incident)')
print('Incident table columns:')
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

print()

# Check Notification table
cursor.execute('PRAGMA table_info(Notification)')
print('Notification table columns:')
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

conn.close()
