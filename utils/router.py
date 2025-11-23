from datetime import datetime
from flask import render_template, request
import utils.database as database

def base_page():
    return render_template('base.html')

def transfers_page():
    submitted = request.args.get("submitted")
    season = request.args.get("season")
    min_fee_raw = request.args.get("min_fee")
    max_fee_raw = request.args.get("max_fee")
    sort_option = request.args.get("sort")

    # Sezonlar kısaltılmış formatta (ör: 24/25) tutuluyor
    seasons = [f"{str(y)[-2:]}/{str(y+1)[-2:]}" for y in range(2025, 2000, -1)]

    def _parse_money(val):
        if val is None or val == "":
            return None
        cleaned = val.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    sort_map = {
        "fee_asc": ("fee", "asc"),
        "fee_desc": ("fee", "desc"),
        "date_asc": ("date", "asc"),
        "date_desc": ("date", "desc"),
    }
    sort_by, sort_dir = sort_map.get(sort_option, ("date", "desc"))

    transfers = []
    if submitted:
        transfers = database.get_transfers(
            season=season,
            min_fee=_parse_money(min_fee_raw),
            max_fee=_parse_money(max_fee_raw),
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    return render_template(
        'transfers.html',
        transfers=transfers,
        filter_applied=bool(submitted),
        seasons=seasons,
        filters={
            "season": season or "",
            "min_fee": min_fee_raw or "",
            "max_fee": max_fee_raw or "",
            "sort": sort_option or "",
        }
    )

def players_page():
    return render_template('players.html')

def games_page():
    current_year = datetime.now().year
    years = list(range(current_year, 2011, -1))
    
    selected_year = request.args.get("year", type=int)
    games = []

    if selected_year and 1900 <= selected_year <= current_year:
        games = database.get_games_by_year(selected_year)

    return render_template(
        'games.html',
        years=years,
        selected_year=selected_year,
        games=games,
    )

def competitions_page():
    """Mücadeleler sayfasını render eder ve veritabanından mücadele verilerini çeker."""
    competitions = database.get_all_competitions()
    return render_template('competitions.html', competitions=competitions)

def clubs_page():
    """Kulüpler sayfasını render eder ve veritabanından kulüp verilerini çeker."""
    clubs = database.get_all_clubs()
    return render_template('clubs.html', clubs=clubs)
