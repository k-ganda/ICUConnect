import psycopg2
from psycopg2 import sql

# Database connection details from your app/__init__.py
DB_URI = 'postgresql://flaskuser:uuitg6oty7bdR9hdL5uTOoIoQTHId4vC@dpg-d1m3n2ali9vc73cot8q0-a.oregon-postgres.render.com:5432/icuconnectdb_vuav'

def cleanup_migrations():
    try:
        # Connect to the database
        print("Connecting to database...")
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()
        
        # Check if alembic_version table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'alembic_version'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("Found alembic_version table. Deleting it...")
            cursor.execute("DROP TABLE alembic_version;")
            conn.commit()
            print("✅ Successfully deleted alembic_version table")
        else:
            print("✅ alembic_version table does not exist")
        
        # Close connection
        cursor.close()
        conn.close()
        print("Database connection closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    cleanup_migrations() 