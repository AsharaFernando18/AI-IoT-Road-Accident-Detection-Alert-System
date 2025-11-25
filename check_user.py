import sqlite3

conn = sqlite3.connect('database/roadsafenet.db')
cursor = conn.cursor()

# Check if user exists
cursor.execute('SELECT id, username, role, telegram_bot_token, telegram_chat_id FROM User WHERE username = ?', ('hospital_kl_demo',))
user = cursor.fetchone()

print('\n=== USER: hospital_kl_demo ===')
if user:
    print(f'ID: {user[0]}')
    print(f'Username: {user[1]}')
    print(f'Role: {user[2]}')
    print(f'Bot Token: {user[3] if user[3] else "(not set)"}')
    print(f'Chat ID: {user[4] if user[4] else "(not set)"}')
else:
    print('❌ User not found!')
    print('\nAvailable users:')
    cursor.execute('SELECT id, username, role FROM User')
    users = cursor.fetchall()
    for u in users:
        print(f'  - {u[1]} (role: {u[2]})')

conn.close()
