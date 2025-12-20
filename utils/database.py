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
    """Returns only id and name for the club selection list."""
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

def get_player_options():
    """Returns player list for the transfer edit form."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT player_id, name
            FROM players
            WHERE name IS NOT NULL
            ORDER BY name ASC
            """
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        print(f"Database error (get_player_options): {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_opponents_for_club(club_id: int):
    """Returns opponents a club has faced (id, name)."""
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
    """Returns match stats for a given year (total matches, goals, averages)."""
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
    """Returns head-to-head stats and recent matches between two clubs."""
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
    """Creates a PostgreSQL connection."""
    DB_URL = os.getenv("DATABASE_URL")
    # print(DB_URL)
    if not DB_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(DB_URL)

def get_all_clubs():
    """Fetches all clubs from the database."""
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
                roster.player_count AS roster_player_count,
                c.average_age,
                c.foreigners_number AS foreign_number,
                c.national_team_players AS national_number,
                c.domestic_competition_id,
                comp.name AS league_name,
                comp.country_name AS league_country,
                comp.is_major_national_league AS is_major_league,
                mv.player_name AS most_valuable_player_name,
                mv.market_value_in_eur AS most_valuable_player_value
            FROM clubs c
            LEFT JOIN competitions comp ON c.domestic_competition_id = comp.competition_id
            LEFT JOIN LATERAL (
                SELECT COUNT(*)::INTEGER AS player_count
                FROM players p
                WHERE p.current_club_id = c.club_id
            ) roster ON TRUE
            LEFT JOIN LATERAL (
                SELECT
                    p.name AS player_name,
                    MAX(t.market_value_in_eur) AS market_value_in_eur
                FROM players p
                LEFT JOIN transfers t ON t.player_id = p.player_id
                WHERE p.current_club_id = c.club_id
                GROUP BY p.player_id, p.name
                ORDER BY MAX(t.market_value_in_eur) DESC NULLS LAST, p.player_id ASC
                LIMIT 1
            ) mv ON TRUE
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
    """Returns league list and min/max summaries for club filters."""
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
    """Returns club data based on filters."""
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
                roster.player_count AS roster_player_count,
                c.average_age,
                c.foreigners_number AS foreign_number,
                c.national_team_players AS national_number,
                c.domestic_competition_id,
                comp.name AS league_name,
                comp.country_name AS league_country,
                comp.is_major_national_league AS is_major_league,
                mv.player_name AS most_valuable_player_name,
                mv.market_value_in_eur AS most_valuable_player_value
            FROM clubs c
            LEFT JOIN competitions comp ON c.domestic_competition_id = comp.competition_id
            LEFT JOIN LATERAL (
                SELECT COUNT(*)::INTEGER AS player_count
                FROM players p
                WHERE p.current_club_id = c.club_id
            ) roster ON TRUE
            LEFT JOIN LATERAL (
                SELECT
                    p.name AS player_name,
                    MAX(t.market_value_in_eur) AS market_value_in_eur
                FROM players p
                LEFT JOIN transfers t ON t.player_id = p.player_id
                WHERE p.current_club_id = c.club_id
                GROUP BY p.player_id, p.name
                ORDER BY MAX(t.market_value_in_eur) DESC NULLS LAST, p.player_id ASC
                LIMIT 1
            ) mv ON TRUE
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
    """Returns a single club row (clubs table)."""
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
    """Updates a single row in the clubs table and returns the updated row."""
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
    """Deletes a single row from the clubs table."""
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
    """Returns clubs in the selected league."""
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
    """Fetches all competitions, optionally filtered by country name and major league status."""
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
    """Fetches all countries from the database (countries with competitions)."""
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
    """Returns transfer leagues sorted by country, excluding 'Europa'."""
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
    """Filters and sorts transfers with optional pagination."""
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
                t.player_id,
                t.from_club_id,
                t.to_club_id,
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
    """Returns transfers containing the given player name in chronological order."""
    if not player_name:
        return []

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT 
                t.transfer_id,
                t.player_id,
                t.from_club_id,
                t.to_club_id,
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


def update_transfer(transfer_id: int, payload: dict) -> bool:
    """Updates a transfer record."""
    if not transfer_id:
        return False

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        query = """
            UPDATE transfers
            SET from_club_id = %s,
                to_club_id = %s,
                transfer_fee = %s,
                market_value_in_eur = %s
            WHERE transfer_id = %s
        """
        params = (
            payload.get("from_club_id"),
            payload.get("to_club_id"),
            payload.get("transfer_fee"),
            payload.get("market_value_in_eur"),
            transfer_id,
        )
        cur.execute(query, params)
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        return updated
    except Exception as e:
        print(f"Database error (update_transfer): {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def delete_transfer(transfer_id: int) -> bool:
    """Deletes a transfer record."""
    if not transfer_id:
        return False

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM transfers WHERE transfer_id = %s", (transfer_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        return deleted
    except Exception as e:
        print(f"Database error (delete_transfer): {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def get_table_schemas():
    """Returns public schema tables and column metadata."""
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
    """Returns column schema for a single table."""
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
    """Inserts a row into the specified table; columns are determined dynamically."""
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
    """Fetches matches for a given year (paginated)."""
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
    """Fetches favorited matches with optional year filter (paginated)."""
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
    """Marks or unmarks a match as favorite."""
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
    """Returns a basic competition list for the match edit form."""
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
    """Updates a game record."""
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
    """Deletes a game record."""
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

def update_competition(competition_id: str, payload: dict) -> bool:
    """Updates a league record."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        name = payload.get("name")
        url = payload.get("url")
        is_major = payload.get("is_major_league")

        cur.execute(
            """
            UPDATE competitions
            SET name = %s,
                url = %s,
                is_major_national_league = %s
            WHERE competition_id = %s
            """,
            (name, url, is_major, competition_id),
        )
        updated = cur.rowcount > 0

        conn.commit()
        cur.close()
        return updated
    except Exception as e:
        print(f"Database error (update_competition): {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def delete_competition(competition_id: str) -> bool:
    """Deletes a league record."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE games SET competition_id = NULL WHERE competition_id = %s",
            (competition_id,),
        )
        cur.execute(
            "UPDATE clubs SET domestic_competition_id = NULL WHERE domestic_competition_id = %s",
            (competition_id,),
        )
        cur.execute("DELETE FROM competitions WHERE competition_id = %s", (competition_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        return deleted
    except Exception as e:
        print(f"Database error (delete_competition): {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()



#----------------------------------PLAYERS------------------------------------------------

def get_all_players(page=1, per_page=100, min_age=None, max_age=None, feet=None, positions=None, sort_option="name_asc", search_query=None, min_mv=None, max_mv=None):
    """
    Fetches players by page, age, foot, position, sort order, and search query.
    """
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        base_where = "WHERE 1=1"
        params = []

        # --- NEW: SEARCH QUERY ---
        if search_query:
            # ILIKE: case-insensitive "contains" search
            base_where += " AND p.name ILIKE %s"
            params.append(f"%{search_query}%")
        # -----------------------------------

        # 1. Filters (existing logic)
        if min_age is not None:
            base_where += " AND DATE_PART('year', AGE(CURRENT_DATE, p.date_of_birth)) >= %s"
            params.append(min_age)
        if max_age is not None:
            base_where += " AND DATE_PART('year', AGE(CURRENT_DATE, p.date_of_birth)) <= %s"
            params.append(max_age)
        if min_mv is not None:
            base_where += " AND p.market_value_in_eur >= %s"
            params.append(min_mv)
        if max_mv is not None:
            base_where += " AND p.market_value_in_eur <= %s"
            params.append(max_mv)
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

        # 2. Sorting
        order_clause = "ORDER BY p.name ASC"
        if sort_option == "name_desc": order_clause = "ORDER BY p.name DESC"
        elif sort_option == "age_asc": order_clause = "ORDER BY p.date_of_birth DESC NULLS LAST"
        elif sort_option == "age_desc": order_clause = "ORDER BY p.date_of_birth ASC NULLS LAST"
        elif sort_option == "height_asc": order_clause = "ORDER BY p.height_in_cm ASC NULLS LAST"
        elif sort_option == "height_desc": order_clause = "ORDER BY p.height_in_cm DESC NULLS LAST"
        elif sort_option == "mv_desc": # € High (expensive to cheap)
            order_clause = "ORDER BY p.market_value_in_eur DESC NULLS LAST"
        elif sort_option == "mv_asc":  # € Low (cheap to expensive)
            order_clause = "ORDER BY p.market_value_in_eur ASC NULLS LAST"

        # 3. Total count (needed to compute total pages for search results)
        count_query = f"SELECT COUNT(*) as total FROM players p {base_where}"
        cur.execute(count_query, params)
        total_count = cur.fetchone()['total']

        # 4. Data fetch
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
                c.name AS club_name,
                p.market_value_in_eur
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
    """Returns the selected club roster."""
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
                p.country_of_citizenship,
                MAX(t.market_value_in_eur) AS market_value_in_eur
            FROM players p
            LEFT JOIN transfers t ON t.player_id = p.player_id
            WHERE p.current_club_id = %s
            GROUP BY
                p.player_id,
                p.name,
                p.date_of_birth,
                p.sub_position,
                p.foot,
                p.height_in_cm,
                p.country_of_citizenship
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
    """Returns a single player record with club and league details."""
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
                p.market_value_in_eur,
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
    """Computes the min and max age in the database."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Query to compute min and max age
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
        
        # If no data, default to 15-45
        if result and result[0] is not None:
            return result[0], result[1]
        return 15, 45
        
    except Exception as e:
        print(f"Database error (get_age_limits): {e}")
        return 15, 45
    finally:
        if conn:
            conn.close()

def get_market_value_limits():
    """Fetches the min and max market value in the database."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Use values greater than 0
        query = """
            SELECT 
                MIN(market_value_in_eur),
                MAX(market_value_in_eur)
            FROM players
            WHERE market_value_in_eur > 0
        """
        
        cur.execute(query)
        result = cur.fetchone()
        cur.close()
        
        # Default values when no data
        if result and result[0] is not None:
            return result[0], result[1]
        return 0, 100000000 # Default 0 - 100M
        
    except Exception as e:
        print(f"Database error (get_market_value_limits): {e}")
        return 0, 100000000
    finally:
        if conn:
            conn.close()

def get_all_positions():
    """Fetches all unique positions (sub_position) from the database."""
    conn = None
    try:
        conn = get_conn()
        print("1")
        cur = conn.cursor() # Dict cursor not needed; returning a list only
        
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
    """Returns stats for the home page (total players, teams, leagues, transfers)."""
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

def get_top_expensive_players(limit=5):
    """Piyasa değeri en yüksek oyuncuları çeker."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT 
                p.player_id,
                p.name,
                p.image_url,
                p.market_value_in_eur,
                p.sub_position,
                c.name AS club_name
            FROM players p
            LEFT JOIN clubs c ON p.current_club_id = c.club_id
            WHERE p.market_value_in_eur IS NOT NULL
            ORDER BY p.market_value_in_eur DESC
            LIMIT %s
        """
        cur.execute(query, (limit,))
        players = cur.fetchall()
        cur.close()
        return players
    except Exception as e:
        print(f"Database error (get_top_expensive_players): {e}")
        return []
    finally:
        if conn:
            conn.close()

# --- ADMIN UPDATE HELPERS ---

def update_player(player_id: int, data: dict):
    """Oyuncu bilgilerini günceller."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        set_parts = []
        values = []
        for key, val in data.items():
            set_parts.append(sql.SQL("{} = %s").format(sql.Identifier(key)))
            values.append(val)
        
        values.append(player_id)
        
        query = sql.SQL("UPDATE players SET {} WHERE player_id = %s").format(
            sql.SQL(", ").join(set_parts)
        )
        
        cur.execute(query, values)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"Database error (update_player): {e}")
        return False
    finally:
        if conn: conn.close()

def get_row_by_id(table_name, id_col, id_val):
    """Admin update ekranı için ID'ye göre tek satır veri çeker."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # SQL Injection koruması için sadece izin verilen tablolar
        allowed_tables = ['clubs', 'competitions', 'games', 'players', 'transfers']
        if table_name not in allowed_tables:
            return None

        query = sql.SQL("SELECT * FROM {} WHERE {} = %s").format(
            sql.Identifier(table_name),
            sql.Identifier(id_col)
        )
        cur.execute(query, (id_val,))
        row = cur.fetchone()
        cur.close()
        return row
    except Exception as e:
        print(f"Error getting row: {e}")
        return None
    finally:
        if conn: conn.close()

def delete_player(player_id: int):
    """Oyuncuyu veritabanından siler."""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM players WHERE player_id = %s", (player_id,))
        conn.commit()
        cur.close()
        return True, None
    except Exception as e:
        print(f"Database error (delete_player): {e}")
        return False, str(e)
    finally:
        if conn: conn.close()