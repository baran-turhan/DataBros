import psycopg2
import os
from typing import Optional
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

from dotenv import load_dotenv

load_dotenv(override=True)


def _game_sort_clause(sort_by: str) -> str:
    """Returns an ORDER BY clause for game queries."""
    if sort_by == "goal_diff_desc":
        return "ORDER BY goal_difference DESC NULLS LAST, g.date ASC, g.game_id ASC"
    if sort_by == "goal_diff_asc":
        return "ORDER BY goal_difference ASC NULLS LAST, g.date ASC, g.game_id ASC"
    return "ORDER BY g.date ASC, g.game_id ASC"

def get_club_options():
    """Kulüp seçim listesi için sadece id ve isim döner."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT club_id, name
            FROM clubs
            WHERE name IS NOT NULL
            ORDER BY name ASC
            """
        )
        clubs = cur.fetchall()
        cur.close()
        return clubs
    except Exception as e:
        print(f"Database error (get_club_options): {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_opponents_for_club(club_id: int):
    """Bir kulübün karşılaştığı rakipleri (id, isim) döner."""
    if not club_id:
        return []

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            WITH opponents AS (
                SELECT DISTINCT
                    CASE 
                        WHEN g.home_club_id = %s THEN g.away_club_id
                        ELSE g.home_club_id
                    END AS opponent_id
                FROM games g
                WHERE g.home_club_id = %s OR g.away_club_id = %s
            )
            SELECT c.club_id, c.name
            FROM opponents o
            JOIN clubs c ON c.club_id = o.opponent_id
            WHERE c.club_id IS NOT NULL
            ORDER BY c.name ASC
            """,
            (club_id, club_id, club_id),
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        print(f"Database error (get_opponents_for_club): {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_game_year_summary(year: int):
    """Belirli bir yılın maç istatistiklerini döner (toplam maç, goller, ortalamalar)."""
    if not year:
        return None

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT
                COUNT(*) AS match_count,
                SUM(COALESCE(g.home_club_goals, 0) + COALESCE(g.away_club_goals, 0)) AS total_goals,
                AVG(
                    CASE 
                        WHEN g.home_club_goals IS NOT NULL AND g.away_club_goals IS NOT NULL 
                        THEN g.home_club_goals + g.away_club_goals 
                    END
                ) AS avg_goals,
                AVG(
                    CASE 
                        WHEN g.home_club_goals IS NOT NULL AND g.away_club_goals IS NOT NULL 
                        THEN ABS(g.home_club_goals - g.away_club_goals) 
                    END
                ) AS avg_goal_diff,
                SUM(CASE WHEN g.home_club_goals = g.away_club_goals AND g.home_club_goals IS NOT NULL THEN 1 ELSE 0 END) AS draws,
                SUM(CASE WHEN g.home_club_goals > g.away_club_goals THEN 1 ELSE 0 END) AS home_wins,
                SUM(CASE WHEN g.away_club_goals > g.home_club_goals THEN 1 ELSE 0 END) AS away_wins,
                MAX(COALESCE(g.home_club_goals, 0) + COALESCE(g.away_club_goals, 0)) AS max_goals_single_match
            FROM games g
            WHERE g.date IS NOT NULL
              AND EXTRACT(YEAR FROM g.date) = %s
            """,
            (year,),
        )
        row = cur.fetchone() or {}
        cur.close()
        if not row:
            return None

        def _maybe_float(value):
            if value is None:
                return None
            try:
                return float(value)
            except Exception:
                return value

        return {
            "match_count": row.get("match_count") or 0,
            "total_goals": row.get("total_goals") or 0,
            "avg_goals": _maybe_float(row.get("avg_goals")),
            "avg_goal_diff": _maybe_float(row.get("avg_goal_diff")),
            "draws": row.get("draws") or 0,
            "home_wins": row.get("home_wins") or 0,
            "away_wins": row.get("away_wins") or 0,
            "max_goals_single_match": row.get("max_goals_single_match") or 0,
        }
    except Exception as e:
        print(f"Database error (get_game_year_summary): {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_head_to_head(club_a_id: int, club_b_id: int, limit: int = 5):
    """İki kulüp arasındaki head-to-head istatistiklerini ve son maçları döner."""
    if not club_a_id or not club_b_id or club_a_id == club_b_id:
        return None, []

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        params = {"a": club_a_id, "b": club_b_id}
        cur.execute(
            """
            SELECT
                COUNT(*) AS match_count,
                SUM(CASE WHEN g.home_club_goals IS NOT NULL AND g.away_club_goals IS NOT NULL AND g.home_club_goals = g.away_club_goals THEN 1 ELSE 0 END) AS draws,
                SUM(
                    CASE 
                        WHEN (g.home_club_id = %(a)s AND g.home_club_goals > g.away_club_goals)
                          OR (g.away_club_id = %(a)s AND g.away_club_goals > g.home_club_goals) 
                        THEN 1 ELSE 0 END
                ) AS club_a_wins,
                SUM(
                    CASE 
                        WHEN (g.home_club_id = %(b)s AND g.home_club_goals > g.away_club_goals)
                          OR (g.away_club_id = %(b)s AND g.away_club_goals > g.home_club_goals) 
                        THEN 1 ELSE 0 END
                ) AS club_b_wins,
                SUM(
                    CASE WHEN g.home_club_id = %(a)s THEN COALESCE(g.home_club_goals, 0) ELSE COALESCE(g.away_club_goals, 0) END
                ) AS club_a_goals,
                SUM(
                    CASE WHEN g.home_club_id = %(a)s THEN COALESCE(g.away_club_goals, 0) ELSE COALESCE(g.home_club_goals, 0) END
                ) AS club_b_goals,
                AVG(ABS(COALESCE(g.home_club_goals, 0) - COALESCE(g.away_club_goals, 0))) AS avg_goal_diff,
                MAX(g.date) AS last_match_date
            FROM games g
            WHERE (g.home_club_id = %(a)s AND g.away_club_id = %(b)s)
               OR (g.home_club_id = %(b)s AND g.away_club_id = %(a)s)
            """,
            params,
        )
        stats_row = cur.fetchone() or {}

        cur.execute(
            """
            SELECT
                g.game_id,
                g.date AS game_date,
                g.home_club_goals,
                g.away_club_goals,
                hc.name AS home_club_name,
                ac.name AS away_club_name,
                comp.name AS competition_name,
                comp.country_name AS competition_country,
                comp.is_major_national_league AS competition_is_major,
                ABS(COALESCE(g.home_club_goals, 0) - COALESCE(g.away_club_goals, 0)) AS goal_difference
            FROM games g
            LEFT JOIN clubs hc ON g.home_club_id = hc.club_id
            LEFT JOIN clubs ac ON g.away_club_id = ac.club_id
            LEFT JOIN competitions comp ON g.competition_id = comp.competition_id
            WHERE (g.home_club_id = %(a)s AND g.away_club_id = %(b)s)
               OR (g.home_club_id = %(b)s AND g.away_club_id = %(a)s)
            ORDER BY g.date DESC NULLS LAST, g.game_id DESC
            LIMIT %(limit)s
            """,
            {"a": club_a_id, "b": club_b_id, "limit": limit},
        )
        matches = cur.fetchall()
        cur.close()

        def _maybe_float(val):
            if val is None:
                return None
            try:
                return float(val)
            except Exception:
                return val

        stats = {
            "match_count": stats_row.get("match_count") or 0,
            "draws": stats_row.get("draws") or 0,
            "club_a_wins": stats_row.get("club_a_wins") or 0,
            "club_b_wins": stats_row.get("club_b_wins") or 0,
            "club_a_goals": stats_row.get("club_a_goals") or 0,
            "club_b_goals": stats_row.get("club_b_goals") or 0,
            "avg_goal_diff": _maybe_float(stats_row.get("avg_goal_diff")),
            "last_match_date": stats_row.get("last_match_date"),
        }

        return stats, matches
    except Exception as e:
        print(f"Database error (get_head_to_head): {e}")
        return None, []
    finally:
        if conn:
            conn.close()

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

def get_club_by_id(club_id: int):
    """Tek bir kulüp satırını (clubs tablosu) döner."""
    if not club_id:
        return None

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM clubs WHERE club_id = %s", (club_id,))
        row = cur.fetchone()
        cur.close()
        return row
    except Exception as e:
        print(f"Database error (get_club_by_id): {e}")
        return None
    finally:
        if conn:
            conn.close()


def update_club(club_id: int, values: dict):
    """clubs tablosunda tek bir satırı günceller ve güncellenmiş satırı döner."""
    if not club_id or not values:
        return None

    values = {k: v for k, v in values.items() if k and k != "club_id"}
    if not values:
        return get_club_by_id(club_id)

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        set_parts = []
        params = []
        for col, val in values.items():
            set_parts.append(sql.SQL("{} = %s").format(sql.Identifier(col)))
            params.append(val)

        query = sql.SQL("UPDATE clubs SET {} WHERE club_id = %s RETURNING *").format(
            sql.SQL(", ").join(set_parts)
        )
        params.append(club_id)

        cur.execute(query, params)
        updated = cur.fetchone()
        conn.commit()
        cur.close()
        return updated
    except Exception as e:
        print(f"Database error (update_club): {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


def delete_club(club_id: int):
    """clubs tablosundan tek bir satırı siler."""
    if not club_id:
        return False, "Invalid club id."

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM clubs WHERE club_id = %s", (club_id,))
        deleted = cur.rowcount or 0
        conn.commit()
        cur.close()
        if deleted == 0:
            return False, "Club not found."
        return True, None
    except Exception as e:
        print(f"Database error (delete_club): {e}")
        if conn:
            conn.rollback()
        return False, str(e)
    finally:
        if conn:
            conn.close()


def get_clubs_by_competition(competition_id: str):
    """Seçilen ligdeki kulüpleri döner."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT 
                c.club_id,
                c.name,
                c.stadium_name,
                c.stadium_seats AS stadium_capacity,
                c.squad_size,
                c.average_age,
                c.foreigners_number AS foreign_number,
                c.national_team_players AS national_number
            FROM clubs c
            WHERE c.domestic_competition_id = %s
            ORDER BY c.name ASC
            """,
            (competition_id,),
        )
        clubs = cur.fetchall()
        cur.close()
        return clubs
    except Exception as e:
        print(f"Database error (get_clubs_by_competition): {e}")
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
        
        query += " ORDER BY c.is_major_national_league DESC, c.name ASC"
        
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
                p.image_url,
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


def get_transfers_by_player_name(player_name: str):
    """Belirtilen oyuncu adını içeren transferleri kronolojik sıralı döner."""
    if not player_name:
        return []

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
                p.image_url,
                t.market_value_in_eur AS player_value,
                p.date_of_birth,
                p.sub_position,
                p.country_of_citizenship,
                fc.name AS from_club,
                fc_comp.name AS from_league,
                tc_comp.name AS to_league,
                tc.name AS to_club
            FROM transfers t
            LEFT JOIN players p ON t.player_id = p.player_id
            LEFT JOIN clubs fc ON t.from_club_id = fc.club_id
            LEFT JOIN clubs tc ON t.to_club_id = tc.club_id
            LEFT JOIN competitions fc_comp ON fc.domestic_competition_id = fc_comp.competition_id
            LEFT JOIN competitions tc_comp ON tc.domestic_competition_id = tc_comp.competition_id
            WHERE p.name ILIKE %s
            ORDER BY t.transfer_date ASC NULLS LAST, t.transfer_id ASC
        """
        cur.execute(query, (f"%{player_name}%",))
        transfers = cur.fetchall()
        cur.close()
        return transfers
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_table_schemas():
    """Public schema tablolarını ve sütun bilgilerini döner."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
        tables = [row["table_name"] for row in cur.fetchall()]

        schemas = []
        for name in tables:
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
                """,
                (name,),
            )
            cols = cur.fetchall()
            schemas.append(
                {
                    "name": name,
                    "columns": [
                        {
                            "name": c["column_name"],
                            "type": c["data_type"],
                            "nullable": c["is_nullable"] == "YES",
                            "default": c["column_default"],
                        }
                        for c in cols
                    ],
                }
            )
        cur.close()
        return schemas
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_table_schema(table_name: str):
    """Tek bir tablo için kolon şemasını döner."""
    if not table_name:
        return None

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        cols = cur.fetchall()
        cur.close()

        if not cols:
            return None

        return {
            "name": table_name,
            "columns": [
                {
                    "name": c["column_name"],
                    "type": c["data_type"],
                    "nullable": c["is_nullable"] == "YES",
                    "default": c["column_default"],
                }
                for c in cols
            ],
        }
    except Exception as e:
        print(f"Database error (get_table_schema): {e}")
        return None
    finally:
        if conn:
            conn.close()


def insert_row(table_name: str, values: dict):
    """Belirtilen tabloya satır ekler; sütunlar dinamik belirlenir."""
    if not table_name or not values:
        return False

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        cols = list(values.keys())
        placeholders = ", ".join(["%s"] * len(cols))
        col_sql = ", ".join([f'"{c}"' for c in cols])
        sql = f'INSERT INTO "{table_name}" ({col_sql}) VALUES ({placeholders})'
        params = [values[c] for c in cols]

        cur.execute(sql, params)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_games_by_year(year: int, sort_by: str = "date", page: int = 1, per_page: int = 100):
    """Belirli bir yıl için maçları getirir (sayfalı)."""
    if not year:
        return [], 0

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        page = page if page and page > 0 else 1
        per_page = per_page if per_page and per_page > 0 else 100

        goal_diff_expr = """
            CASE
                WHEN g.home_club_goals IS NULL OR g.away_club_goals IS NULL THEN NULL
                ELSE ABS(g.home_club_goals - g.away_club_goals)
            END
        """

        order_clause = _game_sort_clause(sort_by)

        count_query = """
            SELECT COUNT(*) AS total
            FROM games g
            WHERE EXTRACT(YEAR FROM g.date) = %s
        """
        cur.execute(count_query, (year,))
        total_count = cur.fetchone()["total"]

        offset = (page - 1) * per_page

        query = """
            SELECT
                g.game_id,
                g.home_club_id,
                g.away_club_id,
                g.competition_id,
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
            LIMIT %s OFFSET %s
        """.format(goal_diff_expr=goal_diff_expr, order_clause=order_clause)

        cur.execute(query, (year, per_page, offset))
        games = cur.fetchall()
        cur.close()
        return games, total_count
    except Exception as e:
        print(f"Database error: {e}")
        return [], 0
    finally:
        if conn:
            conn.close()

def get_favorite_games(
    year: Optional[int] = None,
    sort_by: str = "date",
    page: int = 1,
    per_page: int = 100,
):
    """Favori olarak işaretlenmiş maçları getirir. İsteğe bağlı yıl filtresi uygular (sayfalı)."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        page = page if page and page > 0 else 1
        per_page = per_page if per_page and per_page > 0 else 100

        goal_diff_expr = """
            CASE
                WHEN g.home_club_goals IS NULL OR g.away_club_goals IS NULL THEN NULL
                ELSE ABS(g.home_club_goals - g.away_club_goals)
            END
        """

        order_clause = _game_sort_clause(sort_by)

        base_where = "WHERE g.is_favorite = TRUE"
        params = []

        if year is not None:
            base_where += " AND EXTRACT(YEAR FROM g.date) = %s"
            params.append(year)

        count_query = f"""
            SELECT COUNT(*) AS total
            FROM games g
            {base_where}
        """
        cur.execute(count_query, params)
        total_count = cur.fetchone()["total"]

        offset = (page - 1) * per_page

        query = """
            SELECT
                g.game_id,
                g.home_club_id,
                g.away_club_id,
                g.competition_id,
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
            {base_where}
        """
        query += f" {order_clause} LIMIT %s OFFSET %s"

        cur.execute(
            query.format(goal_diff_expr=goal_diff_expr, base_where=base_where),
            params + [per_page, offset],
        )
        games = cur.fetchall()
        cur.close()
        return games, total_count
    except Exception as e:
        print(f"Database error: {e}")
        return [], 0
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


def get_competition_options():
    """Maç düzenleme formu için basit competition listesi döner."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT competition_id, name, country_name
            FROM competitions
            ORDER BY name ASC
            """
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        print(f"Database error (get_competition_options): {e}")
        return []
    finally:
        if conn:
            conn.close()


def update_game(game_id: int, payload: dict) -> bool:
    """Oyun kaydını günceller."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        query = """
            UPDATE games
            SET home_club_id = %s,
                away_club_id = %s,
                competition_id = %s,
                home_club_goals = %s,
                away_club_goals = %s,
                date = %s,
                home_club_position = %s,
                away_club_position = %s,
                season = %s,
                is_favorite = %s
            WHERE game_id = %s
        """
        params = (
            payload.get("home_club_id"),
            payload.get("away_club_id"),
            payload.get("competition_id"),
            payload.get("home_club_goals"),
            payload.get("away_club_goals"),
            payload.get("date"),
            payload.get("home_club_position"),
            payload.get("away_club_position"),
            payload.get("season"),
            payload.get("is_favorite"),
            game_id,
        )
        cur.execute(query, params)
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        return updated
    except Exception as e:
        print(f"Database error (update_game): {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def delete_game(game_id: int) -> bool:
    """Oyun kaydını siler."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM games WHERE game_id = %s", (game_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        return deleted
    except Exception as e:
        print(f"Database error (delete_game): {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()



#----------------------------------PLAYERS------------------------------------------------

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
                p.player_id,
                p.name,
                p.image_url,
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


def get_players_by_club(club_id: int):
    """Secilen kulup kadrosunu doner."""
    if not club_id:
        return []

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                p.player_id,
                p.name,
                DATE_PART('year', AGE(CURRENT_DATE, p.date_of_birth))::INTEGER AS age,
                p.sub_position,
                p.foot,
                p.height_in_cm,
                p.country_of_citizenship
            FROM players p
            WHERE p.current_club_id = %s
            ORDER BY p.name ASC
        """
        cur.execute(query, (club_id,))
        players = cur.fetchall()
        cur.close()
        return players
    except Exception as e:
        print(f"Database error (get_players_by_club): {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_player_by_id(player_id: int):
    """Tek bir oyuncu kaydini (kulup ve lig bilgisi ile) getirir."""
    if not player_id:
        return None

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT
                p.player_id,
                p.name,
                p.image_url,
                p.date_of_birth,
                DATE_PART('year', AGE(CURRENT_DATE, p.date_of_birth))::INTEGER AS age,
                p.sub_position,
                p.foot,
                p.height_in_cm,
                p.country_of_citizenship,
                c.club_id,
                c.name AS club_name,
                comp.name AS league_name,
                comp.country_name AS league_country
            FROM players p
            LEFT JOIN clubs c ON p.current_club_id = c.club_id
            LEFT JOIN competitions comp ON c.domestic_competition_id = comp.competition_id
            WHERE p.player_id = %s
        """
        cur.execute(query, (player_id,))
        player = cur.fetchone()
        cur.close()
        return player
    except Exception as e:
        print(f"Database error (get_player_by_id): {e}")
        return None
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

def get_statistics():
    """Ana sayfa için istatistikleri döner (toplam oyuncu, takım, lig, transfer sayıları)."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                (SELECT COUNT(*) FROM players) AS total_players,
                (SELECT COUNT(*) FROM clubs) AS total_teams,
                (SELECT COUNT(*) FROM competitions) AS total_leagues,
                (SELECT COUNT(*) FROM games) AS total_games,
                (SELECT COUNT(*) FROM transfers) AS total_transfers
        """
        
        cur.execute(query)
        stats = cur.fetchone()
        cur.close()
        return stats or {
            "total_players": 0,
            "total_teams": 0,
            "total_leagues": 0,
            "total_games": 0,
            "total_transfers": 0
        }
    except Exception as e:
        print(f"Database error (get_statistics): {e}")
        return {
            "total_players": 0,
            "total_teams": 0,
            "total_leagues": 0,
            "total_games": 0,
            "total_transfers": 0
        }
    finally:
        if conn:
            conn.close()

#-----------------------------------------------------------------------------------------
