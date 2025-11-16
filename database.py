import psycopg2
import os
from psycopg2.extras import RealDictCursor

def get_conn():
    """PostgreSQL bağlantısını oluşturur."""
    DB_URL = os.getenv("DATABASE_URL")
    if not DB_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(DB_URL)

def get_all_clubs():
    """Tüm kulüpleri veritabanından çeker."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                club_id,
                name,
                stadium_name,
                stadium_capacity,
                squad_size,
                average_age,
                foreign_number,
                national_number
            FROM clubs
            ORDER BY name ASC
        """
        
        cur.execute(query)
        clubs = cur.fetchall()
        cur.close()
        return clubs
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()

