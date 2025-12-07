import psycopg2
import os
from typing import Optional
from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv

load_dotenv(override=True)


def _game_sort_clause(sort_by: str) -> str:
    """Returns an ORDER BY clause for game queries."""
    if sort_by == "goal_diff_desc":
        return "ORDER BY goal_difference DESC NULLS LAST, g.date ASC, g.game_id ASC"
    if sort_by == "goal_diff_asc":
        return "ORDER BY goal_difference ASC NULLS LAST, g.date ASC, g.game_id ASC"
    return "ORDER BY g.date ASC, g.game_id ASC"

def get_conn():
    """PostgreSQL bağlantısını oluşturur."""
    DB_URL = os.getenv("DATABASE_URL")
    # print(DB_URL)
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
                c.club_id,
                c.name,
                c.stadium_name,
                c.stadium_seats AS stadium_capacity,
                c.squad_size,
                c.average_age,
                c.foreigners_number AS foreign_number,
                c.national_team_players AS national_number,
                c.domestic_competition_id,
                comp.name AS league_name,
                comp.country_name AS league_country,
                comp.is_major_national_league AS is_major_league
            FROM clubs c
            LEFT JOIN competitions comp ON c.domestic_competition_id = comp.competition_id
            ORDER BY c.name ASC
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

def get_club_filter_metadata():
    """Kulüp filtreleri için lig listesi ve min/max özetleri döner."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT DISTINCT comp.name AS league_name
            FROM clubs c
            LEFT JOIN competitions comp ON c.domestic_competition_id = comp.competition_id
            WHERE comp.name IS NOT NULL
            ORDER BY comp.name ASC
            """
        )
        leagues = [row["league_name"] for row in cur.fetchall()]

        cur.execute(
            """
            SELECT
                MIN(average_age) AS min_age,
                MAX(average_age) AS max_age,
                MIN(stadium_seats) AS min_capacity,
                MAX(stadium_seats) AS max_capacity
            FROM clubs
            """
        )
        stats = cur.fetchone() or {}
        cur.close()

        return {
            "leagues": leagues,
            "min_age": stats.get("min_age"),
            "max_age": stats.get("max_age"),
            "min_capacity": stats.get("min_capacity"),
            "max_capacity": stats.get("max_capacity"),
        }
    except Exception as e:
        print(f"Database error (get_club_filter_metadata): {e}")
        return {
            "leagues": [],
            "min_age": None,
            "max_age": None,
            "min_capacity": None,
            "max_capacity": None,
        }
    finally:
        if conn:
            conn.close()

def get_clubs_filtered(search=None, league=None, min_age=None, max_age=None, min_capacity=None, max_capacity=None):
    """Filtrelere göre kulüp verilerini döner."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT 
                c.club_id,
                c.name,
                c.stadium_name,
                c.stadium_seats AS stadium_capacity,
                c.squad_size,
                c.average_age,
                c.foreigners_number AS foreign_number,
                c.national_team_players AS national_number,
                c.domestic_competition_id,
                comp.name AS league_name,
                comp.country_name AS league_country,
                comp.is_major_national_league AS is_major_league
            FROM clubs c
            LEFT JOIN competitions comp ON c.domestic_competition_id = comp.competition_id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND LOWER(c.name) LIKE %s"
            params.append(f"%{search.lower()}%")

        if league:
            query += " AND LOWER(comp.name) = %s"
            params.append(league.lower())

        if min_age is not None:
            query += " AND c.average_age >= %s"
            params.append(min_age)

        if max_age is not None:
            query += " AND c.average_age <= %s"
            params.append(max_age)

        if min_capacity is not None:
            query += " AND c.stadium_seats >= %s"
            params.append(min_capacity)

        if max_capacity is not None:
            query += " AND c.stadium_seats <= %s"
            params.append(max_capacity)

        query += " ORDER BY c.name ASC"

        cur.execute(query, params)
        clubs = cur.fetchall()
        cur.close()
        return clubs
    except Exception as e:
        print(f"Database error (get_clubs_filtered): {e}")
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

def get_transfer_leagues():
    """Transfers için lig listesini ülkeye göre sıralı döner, 'Europa' hariç."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT name, country_name
            FROM competitions
            WHERE competition_id LIKE '%1'
            ORDER BY country_name ASC, name ASC
        """
        cur.execute(query)
        leagues = cur.fetchall()
        cur.close()
        return leagues
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_transfers(
    season=None,
    min_fee=None,
    max_fee=None,
    sort_by=None,
    sort_dir="asc",
    page=None,
    per_page=None,
    from_league=None,
    to_league=None,
):
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
            LEFT JOIN competitions fc_comp ON fc.domestic_competition_id = fc_comp.competition_id
            LEFT JOIN competitions tc_comp ON tc.domestic_competition_id = tc_comp.competition_id
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

        if from_league:
            base_query += " AND fc_comp.name = %s"
            filters.append(from_league)

        if to_league:
            base_query += " AND tc_comp.name = %s"
            filters.append(to_league)

        sort_columns = {
            "fee": "t.transfer_fee",
            "date": "t.transfer_date",
            "value": "t.market_value_in_eur",
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
                fc_comp.name AS from_league,
                tc_comp.name AS to_league,
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

def get_games_by_year(year: int, sort_by: str = "date"):
    """Belirli bir yıl için maçları getirir."""
    if not year:
        return []

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        goal_diff_expr = """
            CASE
                WHEN g.home_club_goals IS NULL OR g.away_club_goals IS NULL THEN NULL
                ELSE ABS(g.home_club_goals - g.away_club_goals)
            END
        """

        order_clause = _game_sort_clause(sort_by)

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
                comp.name AS competition_name,
                comp.country_name AS competition_country,
                comp.is_major_national_league AS competition_is_major,
                {goal_diff_expr} AS goal_difference
            FROM games g
            LEFT JOIN clubs hc ON g.home_club_id = hc.club_id
            LEFT JOIN clubs ac ON g.away_club_id = ac.club_id
            LEFT JOIN competitions comp ON g.competition_id = comp.competition_id
            WHERE EXTRACT(YEAR FROM g.date) = %s
            {order_clause}
        """.format(goal_diff_expr=goal_diff_expr, order_clause=order_clause)

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

def get_favorite_games(year: Optional[int] = None, sort_by: str = "date"):
    """Favori olarak işaretlenmiş maçları getirir. İsteğe bağlı yıl filtresi uygular."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        goal_diff_expr = """
            CASE
                WHEN g.home_club_goals IS NULL OR g.away_club_goals IS NULL THEN NULL
                ELSE ABS(g.home_club_goals - g.away_club_goals)
            END
        """

        order_clause = _game_sort_clause(sort_by)

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
                comp.name AS competition_name,
                comp.country_name AS competition_country,
                comp.is_major_national_league AS competition_is_major,
                {goal_diff_expr} AS goal_difference
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

        query += f" {order_clause}"

        cur.execute(query.format(goal_diff_expr=goal_diff_expr), params)
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



#----------------------------------PLAYERS------------------------------------------------
# utils/database.py içindeki get_all_players fonksiyonunu GÜNCELLE:

def get_all_players(page=1, per_page=100, min_age=None, max_age=None, feet=None, positions=None, sort_option="name_asc", search_query=None):
    """
    Sayfa, yaş, ayak, pozisyon, sıralama ve ARAMA SORGUSUNA göre oyuncuları çeker.
    """
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        base_where = "WHERE 1=1"
        params = []

        # --- YENİ EKLENEN: ARAMA SORGUSU ---
        if search_query:
            # ILIKE: Büyük/Küçük harf duyarsız 'içinde geçiyor mu' araması
            base_where += " AND p.name ILIKE %s"
            params.append(f"%{search_query}%")
        # -----------------------------------

        # 1. Filtreler (Mevcut kodlar)
        if min_age is not None:
            base_where += " AND DATE_PART('year', AGE(CURRENT_DATE, p.date_of_birth)) >= %s"
            params.append(min_age)
        if max_age is not None:
            base_where += " AND DATE_PART('year', AGE(CURRENT_DATE, p.date_of_birth)) <= %s"
            params.append(max_age)
        if feet and len(feet) > 0:
            foot_conditions = []
            if 'None' in feet:
                foot_conditions.append("p.foot IS NULL")
                feet = [f for f in feet if f != 'None']
            if len(feet) > 0:
                feet_lower = [f.lower() for f in feet]
                foot_conditions.append("LOWER(p.foot) = ANY(%s)")
                params.append(feet_lower)
            if foot_conditions:
                base_where += " AND (" + " OR ".join(foot_conditions) + ")"
        if positions and len(positions) > 0:
            if 'All' not in positions:
                base_where += " AND p.sub_position = ANY(%s)"
                params.append(positions)

        # 2. Sıralama
        order_clause = "ORDER BY p.name ASC"
        if sort_option == "name_desc": order_clause = "ORDER BY p.name DESC"
        elif sort_option == "age_asc": order_clause = "ORDER BY p.date_of_birth DESC NULLS LAST"
        elif sort_option == "age_desc": order_clause = "ORDER BY p.date_of_birth ASC NULLS LAST"
        elif sort_option == "height_asc": order_clause = "ORDER BY p.height_in_cm ASC NULLS LAST"
        elif sort_option == "height_desc": order_clause = "ORDER BY p.height_in_cm DESC NULLS LAST"

        # 3. Toplam Sayı (Arama sonuçlarına göre toplam sayfa sayısını hesaplamak için önemli)
        count_query = f"SELECT COUNT(*) as total FROM players p {base_where}"
        cur.execute(count_query, params)
        total_count = cur.fetchone()['total']

        # 4. Veri Çekme
        offset = (page - 1) * per_page
        
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
            {order_clause}
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

def get_all_positions():
    """Veritabanındaki tüm benzersiz pozisyonları (sub_position) çeker."""
    conn = None
    try:
        conn = get_conn()
        print("1")
        cur = conn.cursor() # Dict cursor gerekmez, sadece liste döneceğiz
        
        query = """
            SELECT DISTINCT sub_position 
            FROM players 
            WHERE sub_position IS NOT NULL 
            ORDER BY sub_position ASC
        """
        
        cur.execute(query)
        positions = [row[0] for row in cur.fetchall()]
        cur.close()
        return positions
    except Exception as e:
        print(f"Database error (get_all_positions): {e}")
        return []
    finally:
        if conn:
            conn.close()

#-----------------------------------------------------------------------------------------
