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

def get_all_competitions():
    """Tüm mücadeleleri veritabanından çeker."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                c.competition_id,
                c.name,
                c.is_major_league,
                c.url,
                co.name AS country_name
            FROM competitions c
            LEFT JOIN countries co ON c.country_id = co.country_id
            ORDER BY c.name ASC
        """
        
        cur.execute(query)
        competitions = cur.fetchall()
        cur.close()
        return competitions
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


# database.py dosyasının en altına ekle:

def get_all_players():
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                p.name,
                p.date_of_birth,
                p.sub_position,
                p.foot,
                p.height_in_cm,
                p.country_of_citizenship,
                c.name AS club_name
            FROM players p
            LEFT JOIN clubs c ON p.current_club_id = c.club_id
            ORDER BY p.name ASC
        """
        
        cur.execute(query)
        players = cur.fetchall()
        cur.close()
        return players
    except Exception as e:
        print(f"Database error (get_all_players): {e}")
        return []
    finally:
        if conn:
            conn.close()
