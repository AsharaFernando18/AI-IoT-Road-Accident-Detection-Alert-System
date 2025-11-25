import sqlite3

conn = sqlite3.connect('database/database/roadsafenet.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT username, telegram_bot_token, telegram_chat_id 
    FROM User 
    WHERE username IN ('hospital_kl_demo', 'police_klcc_demo', 'ambulance_klcc_demo')
''')

users = cursor.fetchall()

print('\n📋 DEMO USERS TELEGRAM CREDENTIALS:\n')
print('='*100)
for user in users:
    token = user[1][:30] + '...' if user[1] else 'NOT SET'
    chat_id = user[2] if user[2] else 'NOT SET'
    status = '✅ READY' if user[1] and user[2] else '❌ INCOMPLETE'
    print(f'{status} {user[0]:25} | Token: {token:35} | Chat ID: {chat_id}')
print('='*100)

conn.close()
