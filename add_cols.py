import sqlite3
conn = sqlite3.connect('goldenhour.db')
cursor = conn.cursor()

def add_col(table, col_def):
    try:
        cursor.execute(f'ALTER TABLE {table} ADD COLUMN {col_def}')
        print(f'Added {col_def} to {table}')
    except sqlite3.OperationalError as e:
        print(f'Error adding {col_def} to {table}: {e}')

add_col('users', 'city VARCHAR(100) DEFAULT "Jaipur" NOT NULL')
add_col('users', 'avatar_url VARCHAR(500)')
add_col('users', 'admin_team VARCHAR(100)')

add_col('donors', 'pickup_address VARCHAR(500)')
add_col('donors', 'food_category VARCHAR(200)')
add_col('donors', 'contact_person VARCHAR(255)')
add_col('donors', 'operating_hours VARCHAR(100)')

add_col('recipient_orgs', 'contact_person VARCHAR(255)')
add_col('recipient_orgs', 'contact_phone VARCHAR(32)')
add_col('recipient_orgs', 'max_capacity_portions INTEGER DEFAULT 150 NOT NULL')
add_col('recipient_orgs', 'food_restrictions VARCHAR(255)')
add_col('recipient_orgs', 'receiving_hours VARCHAR(100)')

add_col('drivers', 'vehicle_number VARCHAR(50)')
add_col('drivers', 'operating_area VARCHAR(255)')

conn.commit()
conn.close()
