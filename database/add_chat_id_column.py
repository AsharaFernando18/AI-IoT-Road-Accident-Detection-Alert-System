import sqlite3

conn = sqlite3.connect('database/roadsafenet.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE User ADD COLUMN telegram_chat_id TEXT')
    conn.commit()
    print('✅ telegram_chat_id column added successfully!')
except Exception as e:
    print(f'⚠️  Column might already exist: {e}')

conn.close()
