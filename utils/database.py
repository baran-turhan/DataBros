import psycopg2
import os
from typing import Optional
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

def get_transfers(season=None, min_fee=None, max_fee=None, sort_by=None, sort_dir="asc", page=None, per_page=None):
    """Transferleri isteğe göre filtreleyip sıralar, opsiyonel sayfalama uygular."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        base_query = """
            FROM transfers t
            LEFT JOIN players p ON t.player_id = p.player_id
            LEFT JOIN clubs fc ON t.from_club_id = fc.club_id
            LEFT JOIN clubs tc ON t.to_club_id = tc.club_id
            WHERE 1=1
        """
        filters = []

        if season:
            base_query += " AND t.transfer_season = %s"
            filters.append(season)

        if min_fee is not None:
            base_query += " AND t.transfer_fee >= %s"
            filters.append(min_fee)

        if max_fee is not None:
            base_query += " AND t.transfer_fee <= %s"
            filters.append(max_fee)

        sort_columns = {
            "fee": "t.transfer_fee",
            "date": "t.transfer_date"
        }
        sort_column = sort_columns.get(sort_by, "t.transfer_date")
        sort_direction = "DESC" if str(sort_dir).lower() == "desc" else "ASC"

        count_query = "SELECT COUNT(*) " + base_query
        cur.execute(count_query, filters)
        total_count = cur.fetchone()["count"]

        data_query = f"""
            SELECT 
                t.transfer_id,
                t.transfer_season,
                t.transfer_fee,
                t.transfer_fee AS transfer_fee_value,
                t.transfer_date,
                t.market_value_in_eur,
                p.name AS player_name,
                t.market_value_in_eur AS player_value,
                p.date_of_birth,
                p.sub_position,
                p.country_of_citizenship,
                fc.name AS from_club,
                tc.name AS to_club
            {base_query}
            ORDER BY {sort_column} {sort_direction}
        """

        params = list(filters)
        if page and per_page:
            offset = max(page - 1, 0) * per_page
            data_query += " LIMIT %s OFFSET %s"
            params.extend([per_page, offset])

        cur.execute(data_query, params)
        transfers = cur.fetchall()
        cur.close()
        return transfers, total_count
    except Exception as e:
        print(f"Database error: {e}")
        return [], 0
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
                g.is_favorite,
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

def get_favorite_games(year: Optional[int] = None):
    """Favori olarak işaretlenmiş maçları getirir. İsteğe bağlı yıl filtresi uygular."""
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
                g.is_favorite,
                hc.name AS home_club_name,
                ac.name AS away_club_name,
                comp.name AS competition_name
            FROM games g
            LEFT JOIN clubs hc ON g.home_club_id = hc.club_id
            LEFT JOIN clubs ac ON g.away_club_id = ac.club_id
            LEFT JOIN competitions comp ON g.competition_id = comp.competition_id
            WHERE g.is_favorite = TRUE
        """
        params = []

        if year is not None:
            query += " AND EXTRACT(YEAR FROM g.date) = %s"
            params.append(year)

        query += " ORDER BY g.date ASC, g.game_id ASC"

        cur.execute(query, params)
        games = cur.fetchall()
        cur.close()
        return games
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()

def set_game_favorite(game_id: int, is_favorite: bool = True) -> bool:
    """Bir maçı favori olarak işaretler veya kaldırır."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        query = "UPDATE games SET is_favorite = %s WHERE game_id = %s"
        cur.execute(query, (is_favorite, game_id))
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        return updated
    except Exception as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()




def get_all_players(page=1, per_page=100, min_age=None, max_age=None, feet=None):
    """
    Sayfa, yaş ve ayak filtresine göre oyuncuları çeker.
    feet: Seçilen ayakların listesi (Örn: ['Right', 'Left', 'None'])
    """
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        base_where = "WHERE 1=1"
        params = []

        # 1. Yaş Filtresi
        if min_age is not None:
            base_where += " AND DATE_PART('year', AGE(CURRENT_DATE, p.date_of_birth)) >= %s"
            params.append(min_age)
        
        if max_age is not None:
            base_where += " AND DATE_PART('year', AGE(CURRENT_DATE, p.date_of_birth)) <= %s"
            params.append(max_age)

        # 2. Ayak Filtresi (Çoklu Seçim)
        if feet and len(feet) > 0:
            foot_conditions = []
            
            # Eğer listede 'None' varsa, NULL değerleri de arayalım
            if 'None' in feet:
                foot_conditions.append("p.foot IS NULL")
                # Listeden 'None' stringini çıkar
                feet = [f for f in feet if f != 'None']
            
            # Geriye kalan normal değerler (Right, Left -> right, left yapalım)
            if len(feet) > 0:
                # Gelen değerleri küçük harfe çeviriyoruz (DB uyumu için)
                feet_lower = [f.lower() for f in feet]
                
                # DB'deki veriyi de LOWER() ile küçültüp karşılaştırıyoruz
                foot_conditions.append("LOWER(p.foot) = ANY(%s)")
                params.append(feet_lower)
            
            # Koşulları birleştir
            if foot_conditions:
                base_where += " AND (" + " OR ".join(foot_conditions) + ")"

        # Toplam sayı
        count_query = f"SELECT COUNT(*) as total FROM players p {base_where}"
        cur.execute(count_query, params)
        total_count = cur.fetchone()['total']

        # OFFSET
        offset = (page - 1) * per_page
        
        # Oyuncuları çek
        query = f"""
            SELECT 
                p.name,
                p.date_of_birth,
                DATE_PART('year', AGE(CURRENT_DATE, p.date_of_birth))::INTEGER AS age,
                p.sub_position,
                p.foot,
                p.height_in_cm,
                p.country_of_citizenship,
                c.name AS club_name
            FROM players p
            LEFT JOIN clubs c ON p.current_club_id = c.club_id
            {base_where}
            ORDER BY p.name ASC
            LIMIT %s OFFSET %s
        """
        
        query_params = params + [per_page, offset]
        
        cur.execute(query, query_params)
        players = cur.fetchall()
        
        cur.close()
        return players, total_count
        
    except Exception as e:
        print(f"Database error (get_all_players): {e}")
        return [], 0
    finally:
        if conn:
            conn.close()


def get_age_limits():
    """Veritabanındaki en küçük ve en büyük yaşı hesaplar."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # En küçük ve en büyük yaşı hesaplayan sorgu
        query = """
            SELECT 
                MIN(DATE_PART('year', AGE(CURRENT_DATE, date_of_birth)))::INTEGER as min_age,
                MAX(DATE_PART('year', AGE(CURRENT_DATE, date_of_birth)))::INTEGER as max_age
            FROM players
            WHERE date_of_birth IS NOT NULL
        """
        
        cur.execute(query)
        result = cur.fetchone()
        cur.close()
        
        # Eğer veri yoksa varsayılan olarak 15-45 döndür
        if result and result[0] is not None:
            return result[0], result[1]
        return 15, 45
        
    except Exception as e:
        print(f"Database error (get_age_limits): {e}")
        return 15, 45
    finally:
        if conn:
            conn.close()