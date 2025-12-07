from datetime import datetime
from flask import render_template, request, jsonify
import utils.database as database

def base_page():
    return render_template('base.html')

def transfers_page():
    submitted = request.args.get("submitted")
    season = request.args.get("season")
    min_fee_raw = request.args.get("min_fee")
    max_fee_raw = request.args.get("max_fee")
    sort_option = request.args.get("sort")
    from_league = request.args.get("from_league")
    to_league = request.args.get("to_league")
    page = request.args.get("page", default=1, type=int)
    per_page = 20

    # Sezonlar kısaltılmış formatta (ör: 24/25) tutuluyor
    seasons = [f"{str(y)[-2:]}/{str(y+1)[-2:]}" for y in range(2025, 2000, -1)]

    def _format_league_name(name: str) -> str:
        if not name:
            return ""
        return name.replace("-", " ").replace("_", " ").title()

    leagues_raw = database.get_transfer_leagues()
    leagues = [
        {
            "value": row.get("name"),
            "label": _format_league_name(row.get("name")),
            "country": row.get("country_name"),
        }
        for row in leagues_raw
    ]

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
        "value_asc": ("value", "asc"),
        "value_desc": ("value", "desc"),
        "date_asc": ("date", "asc"),
        "date_desc": ("date", "desc"),
    }
    sort_by, sort_dir = sort_map.get(sort_option, ("date", "desc"))

    transfers = []
    total_results = 0
    current_page = page if page and page > 0 else 1
    if submitted:
        transfers_raw, total_results = database.get_transfers(
            season=season,
            min_fee=_parse_money(min_fee_raw),
            max_fee=_parse_money(max_fee_raw),
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=current_page,
            per_page=per_page,
            from_league=from_league,
            to_league=to_league,
        )
        def _calc_age(dob):
            if not dob:
                return None
            today = datetime.utcnow().date()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        transfers = []
        for t in transfers_raw:
            t["age"] = _calc_age(t.get("date_of_birth"))
            transfers.append(t)

    total_pages = 0
    if submitted and total_results:
        total_pages = (total_results + per_page - 1) // per_page

    return render_template(
        'transfers.html',
        transfers=transfers,
        filter_applied=bool(submitted),
        seasons=seasons,
        page=current_page,
        total_pages=total_pages,
        total_results=total_results,
        per_page=per_page,
        filters={
            "season": season or "",
            "min_fee": min_fee_raw or "",
            "max_fee": max_fee_raw or "",
            "sort": sort_option or "",
            "from_league": from_league or "",
            "to_league": to_league or "",
        },
        leagues=leagues,
    )




def players_page():
    page = request.args.get('page', 1, type=int)
    per_page = 100
    search_query = (request.args.get('search') or '').strip()
    
    # Filtreleri al
    min_age = request.args.get('min_age', type=int)
    max_age = request.args.get('max_age', type=int)
    selected_feet = request.args.getlist('foot')
    selected_positions = request.args.getlist('position')
    
    # YENİ: Sıralama parametresini al (Varsayılan: name_asc)
    sort_option = request.args.get('sort', 'name_asc')
    
    # Veritabanına gönder
    players, total_count = database.get_all_players(
        page, per_page, min_age, max_age, selected_feet, selected_positions, sort_option
    )
    
    # Ekstra Bilgiler
    global_min_age, global_max_age = database.get_age_limits()
    all_positions = database.get_all_positions()
    total_pages = (total_count + per_page - 1) // per_page
    
    return render_template(
        'players.html', 
        players=players, 
        current_page=page, 
        total_pages=total_pages,
        selected_min_age=min_age,
        selected_max_age=max_age,
        global_min_age=global_min_age,
        global_max_age=global_max_age,
        selected_feet=selected_feet,
        selected_positions=selected_positions,
        # YENİ: Sıralama bilgisini şablona gönder
        current_sort=sort_option,
        all_positions=all_positions,
        search_query=search_query,
    )


def games_page():
    current_year = datetime.now().year
    years = list(range(current_year, 2011, -1))
    
    selected_year = request.args.get("year", type=int)
    favorite_only_param = request.args.get("favorites")
    favorite_only = str(favorite_only_param).lower() in ("1", "true", "yes")
    sort_option = request.args.get("sort", "date")
    if sort_option not in ("date", "goal_diff_desc", "goal_diff_asc"):
        sort_option = "date"
    games = []

    if favorite_only:
        if selected_year and 1900 <= selected_year <= current_year:
            games = database.get_favorite_games(selected_year, sort_by=sort_option)
        else:
            selected_year = None
            games = database.get_favorite_games(sort_by=sort_option)
    elif selected_year and 1900 <= selected_year <= current_year:
        games = database.get_games_by_year(selected_year, sort_by=sort_option)

    # Gol farkı bilgisini önden hesaplayıp front-end'de filtreleme için saklıyoruz
    for game in games:
        if game.get("goal_difference") is None:
            home_goals = game.get("home_club_goals")
            away_goals = game.get("away_club_goals")
            if home_goals is not None and away_goals is not None:
                game["goal_difference"] = abs(home_goals - away_goals)

    return render_template(
        'games.html',
        years=years,
        selected_year=selected_year,
        games=games,
        favorite_only=favorite_only,
        sort_option=sort_option,
    )

def update_game_favorite(game_id: int):
    """Bir maçı favori olarak işaretler."""
    success = database.set_game_favorite(game_id, True)
    if not success:
        return jsonify({"success": False, "message": "Güncelleme yapılamadı."}), 500
    return jsonify({"success": True, "is_favorite": True})

def competitions_page():
    """Mücadeleler sayfasını render eder ve veritabanından mücadele verilerini çeker."""
    selected_country = request.args.get("country")
    is_major_league_param = request.args.get("is_major_league")
    countries = database.get_all_countries()
    competitions = []
    
    # Parse is_major_league parameter (can be "true", "false", or None)
    is_major_league = None
    if is_major_league_param == "true":
        is_major_league = True
    elif is_major_league_param == "false":
        is_major_league = False
    
    if selected_country:
        competitions = database.get_all_competitions(
            country_name=selected_country,
            is_major_league=is_major_league
        )
    
    return render_template(
        'competitions.html',
        competitions=competitions,
        countries=countries,
        selected_country=selected_country,
        selected_is_major_league=is_major_league_param,
    )

def clubs_page():
    """Kulüpler sayfasını render eder ve veritabanından kulüp verilerini çeker."""
    filters_metadata = database.get_club_filter_metadata()

    search_query = (request.args.get("search") or "").strip()
    league_filter = (request.args.get("league") or "").strip()
    min_age_raw = request.args.get("min_age")
    max_age_raw = request.args.get("max_age")
    min_capacity_raw = request.args.get("min_capacity")
    max_capacity_raw = request.args.get("max_capacity")
    submitted = request.args.get("submitted")

    def _parse_float(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    def _parse_int(val):
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    selected_min_age = _parse_float(min_age_raw)
    selected_max_age = _parse_float(max_age_raw)
    selected_min_capacity = _parse_int(min_capacity_raw)
    selected_max_capacity = _parse_int(max_capacity_raw)

    filter_applied = bool(submitted) or any(
        [
            search_query,
            league_filter,
            min_age_raw not in (None, ""),
            max_age_raw not in (None, ""),
            min_capacity_raw not in (None, ""),
            max_capacity_raw not in (None, ""),
        ]
    )

    clubs = []
    if filter_applied:
        clubs = database.get_clubs_filtered(
            search=search_query or None,
            league=league_filter or None,
            min_age=selected_min_age,
            max_age=selected_max_age,
            min_capacity=selected_min_capacity,
            max_capacity=selected_max_capacity,
        )

    return render_template(
        "clubs.html",
        clubs=clubs,
        leagues=filters_metadata.get("leagues", []),
        min_age=filters_metadata.get("min_age"),
        max_age=filters_metadata.get("max_age"),
        min_capacity=filters_metadata.get("min_capacity"),
        max_capacity=filters_metadata.get("max_capacity"),
        search_query=search_query,
        selected_league=league_filter,
        selected_min_age=selected_min_age,
        selected_max_age=selected_max_age,
        selected_min_capacity=selected_min_capacity,
        selected_max_capacity=selected_max_capacity,
        filter_applied=filter_applied,
    )
