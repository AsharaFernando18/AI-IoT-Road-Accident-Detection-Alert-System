import sqlite3

print('\n🔧 Adding telegram_chat_id column to database/database/roadsafenet.db...\n')

conn = sqlite3.connect('database/database/roadsafenet.db')
cursor = conn.cursor()

try:
    # Check if column exists
    cursor.execute('PRAGMA table_info(User)')
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'telegram_chat_id' in columns:
        print('✅ telegram_chat_id column already exists')
    else:
        # Add telegram_chat_id column
        cursor.execute('ALTER TABLE User ADD COLUMN telegram_chat_id TEXT')
        conn.commit()
        print('✅ telegram_chat_id column added successfully!')
    
    # Verify
    cursor.execute('PRAGMA table_info(User)')
    columns = cursor.fetchall()
    print('\n📋 User table columns:')
    for col in columns:
        print(f'   - {col[1]} ({col[2]})')
    
except Exception as e:
    print(f'❌ Error: {e}')

conn.close()
