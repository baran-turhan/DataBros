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

def get_games_by_year(year: int):
    """Belirli bir yıl için maçları getirir."""
    if not year:
        return []

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                g.game_id,
                g.date AS game_date,
                g.home_club_goals,
                g.away_club_goals,
                g.season,
                g.home_club_position,
                g.away_club_position,
                hc.name AS home_club_name,
                ac.name AS away_club_name,
                comp.name AS competition_name
            FROM games g
            LEFT JOIN clubs hc ON g.home_club_id = hc.club_id
            LEFT JOIN clubs ac ON g.away_club_id = ac.club_id
            LEFT JOIN competitions comp ON g.competition_id = comp.competition_id
            WHERE EXTRACT(YEAR FROM g.date) = %s
            ORDER BY g.date ASC, g.game_id ASC
        """

        cur.execute(query, (year,))
        games = cur.fetchall()
        cur.close()
        return games
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()
