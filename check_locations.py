import sqlite3

conn = sqlite3.connect('database/roadsafenet.db')
cursor = conn.cursor()

# Check counts
cursor.execute('SELECT COUNT(*) as total, COUNT(city) as with_city, COUNT(location_name) as with_location FROM Accident')
result = cursor.fetchone()
print(f'\nTotal accidents: {result[0]}')
print(f'With city: {result[1]}')  
print(f'With location_name: {result[2]}')

# Check first 5 records
cursor.execute('SELECT city, location_name FROM Accident LIMIT 5')
print('\nFirst 5 records:')
for row in cursor.fetchall():
    print(f'  City: "{row[0]}", Location: "{row[1]}"')

conn.close()
