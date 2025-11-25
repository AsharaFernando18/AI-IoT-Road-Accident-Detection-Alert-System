import sqlite3

conn = sqlite3.connect('database/database/roadsafenet.db')
cursor = conn.cursor()

cursor.execute('SELECT id, username, role, telegram_bot_token, telegram_chat_id FROM User WHERE username IN (?, ?, ?)', 
               ('hospital_kl_demo', 'police_klcc_demo', 'ambulance_klcc_demo'))
users = cursor.fetchall()

print('\n=== DEMO USERS IN CORRECT DATABASE ===')
for u in users:
    token_set = "✓ Set" if u[3] else "✗ Not set"
    chat_id_set = "✓ Set" if u[4] else "✗ Not set"
    print(f'ID: {u[0]:2d} | Username: {u[1]:20s} | Role: {u[2]:10s} | Token: {token_set} | Chat ID: {chat_id_set}')

conn.close()
