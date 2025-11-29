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
                stadium_seats AS stadium_capacity,
                squad_size,
                average_age,
                foreigners_number AS foreign_number,
                national_team_players AS national_number
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

def get_all_competitions(country_name=None, is_major_league=None):
    """Tüm mücadeleleri veritabanından çeker. İsteğe bağlı olarak ülke adına ve major league durumuna göre filtreler."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                c.competition_id,
                c.name,
                c.is_major_national_league AS is_major_league,
                c.url,
                c.country_name
            FROM competitions c
            WHERE 1=1
        """
        params = []
        
        if country_name:
            query += " AND c.country_name = %s"
            params.append(country_name)
        
        if is_major_league is not None:
            query += " AND c.is_major_national_league = %s"
            params.append(is_major_league)
        
        query += " ORDER BY c.name ASC"
        
        cur.execute(query, params)
        competitions = cur.fetchall()
        cur.close()
        return competitions
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_all_countries():
    """Tüm ülkeleri veritabanından çeker (mücadeleleri olan ülkeler)."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT DISTINCT c.country_name
            FROM competitions c
            WHERE c.country_name IS NOT NULL
            ORDER BY c.country_name ASC
        """
        
        cur.execute(query)
        countries = cur.fetchall()
        cur.close()
        return [row['country_name'] for row in countries]
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_transfers(season=None, min_fee=None, max_fee=None, sort_by=None, sort_dir="asc"):
    """Transferleri isteğe göre filtreleyip sıralar."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT 
                t.transfer_id,
                t.transfer_season,
                t.transfer_fee,
                t.transfer_fee AS transfer_fee_value,
                t.transfer_date,
                t.market_value_in_eur,
                p.name AS player_name,
                fc.name AS from_club,
                tc.name AS to_club
            FROM transfers t
            LEFT JOIN players p ON t.player_id = p.player_id
            LEFT JOIN clubs fc ON t.from_club_id = fc.club_id
            LEFT JOIN clubs tc ON t.to_club_id = tc.club_id
            WHERE 1=1
        """
        params = []

        if season:
            query += " AND t.transfer_season = %s"
            params.append(season)

        if min_fee is not None:
            query += " AND t.transfer_fee >= %s"
            params.append(min_fee)

        if max_fee is not None:
            query += " AND t.transfer_fee <= %s"
            params.append(max_fee)

        sort_columns = {
            "fee": "t.transfer_fee",
            "date": "t.transfer_date"
        }
        sort_column = sort_columns.get(sort_by, "t.transfer_date")
        sort_direction = "DESC" if str(sort_dir).lower() == "desc" else "ASC"

        query += f" ORDER BY {sort_column} {sort_direction}"

        cur.execute(query, params)
        transfers = cur.fetchall()
        cur.close()
        return transfers
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
