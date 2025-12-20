from datetime import datetime
from flask import render_template, request, jsonify, abort
import utils.database as database

def base_page():
    """Ana sayfa için verileri çeker ve render eder."""
    # Major leagues (top 8 for featured section)
    major_leagues = database.get_all_competitions(is_major_league=True)[:8]
    
    # Statistics for quick stats cards
    stats = database.get_statistics()
    
    return render_template(
        'base.html',
        major_leagues=major_leagues,
        stats=stats
    )

def transfers_page():
    submitted = request.args.get("submitted")
    season = request.args.get("season")
    min_fee_raw = request.args.get("min_fee")
    max_fee_raw = request.args.get("max_fee")
    sort_option = request.args.get("sort")
    from_league = request.args.get("from_league")
    to_league = request.args.get("to_league")
    page = request.args.get("page", default=1, type=int)
    player_query = (request.args.get("player_name") or "").strip()
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

    def _calc_age(dob):
        if not dob:
            return None
        today = datetime.utcnow().date()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    club_options = database.get_club_options()

    player_transfers = []
    if player_query:
        player_transfers_raw = database.get_transfers_by_player_name(player_query)
        for t in player_transfers_raw:
            t["age"] = _calc_age(t.get("date_of_birth"))
            player_transfers.append(t)

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
        player_query=player_query,
        player_search_applied=bool(player_query),
        player_transfers=player_transfers,
        club_options=club_options,
    )




# utils/router.py içindeki players_page fonksiyonunu GÜNCELLE:

def players_page():
    page = request.args.get('page', 1, type=int)
    per_page = 100
    
    # Filtreleri al
    min_age = request.args.get('min_age', type=int)
    max_age = request.args.get('max_age', type=int)
    selected_feet = request.args.getlist('foot')
    selected_positions = request.args.getlist('position')
    sort_option = request.args.get('sort', 'name_asc')
    
    # YENİ: Arama sorgusunu al
    search_query = request.args.get('search', '')
    
    # Veritabanına search_query'i de gönderiyoruz
    players, total_count = database.get_all_players(
        page, per_page, min_age, max_age, selected_feet, selected_positions, sort_option, search_query
    )
    
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
        current_sort=sort_option,
        all_positions=all_positions,
        # YENI: Arama metnini sablona geri gonder (input icinde kalsin diye)
        search_query=search_query
    )


def player_profile_page(player_id: int):
    """Single player profile page."""
    player = database.get_player_by_id(player_id)
    if not player:
        abort(404)
    return render_template("player_profile.html", player=player)


def games_page():
    current_year = datetime.now().year
    years = list(range(current_year, 2011, -1))
    
    selected_year = request.args.get("year", type=int)
    club_a_id = request.args.get("club_a", type=int)
    club_b_id = request.args.get("club_b", type=int)
    favorite_only_param = request.args.get("favorites")
    favorite_only = str(favorite_only_param).lower() in ("1", "true", "yes")
    sort_option = request.args.get("sort", "date")
    if sort_option not in ("date", "goal_diff_desc", "goal_diff_asc"):
        sort_option = "date"
    page = request.args.get("page", default=1, type=int)
    per_page = 100
    if page < 1:
        page = 1

    games = []
    year_summary = None
    total_results = 0

    # Kulüp listesi head-to-head formu için
    club_options = database.get_club_options()
    club_name_map = {c["club_id"]: c["name"] for c in club_options} if club_options else {}
    opponent_options = []
    competition_options = database.get_competition_options()

    head_to_head_stats = None
    head_to_head_matches = []
    head_to_head_error = None

    if favorite_only:
        if selected_year and 1900 <= selected_year <= current_year:
            games, total_results = database.get_favorite_games(
                selected_year,
                sort_by=sort_option,
                page=page,
                per_page=per_page,
            )
        else:
            selected_year = None
            games, total_results = database.get_favorite_games(
                sort_by=sort_option,
                page=page,
                per_page=per_page,
            )
    elif selected_year and 1900 <= selected_year <= current_year:
        games, total_results = database.get_games_by_year(
            selected_year,
            sort_by=sort_option,
            page=page,
            per_page=per_page,
        )
        year_summary = database.get_game_year_summary(selected_year)

    # Gol farkı bilgisini önden hesaplayıp front-end'de filtreleme için saklıyoruz
    for game in games:
        if game.get("goal_difference") is None:
            home_goals = game.get("home_club_goals")
            away_goals = game.get("away_club_goals")
            if home_goals is not None and away_goals is not None:
                game["goal_difference"] = abs(home_goals - away_goals)

    if club_a_id:
        opponent_options = database.get_opponents_for_club(club_a_id) or []
        valid_opponent_ids = {row["club_id"] for row in opponent_options}
    else:
        valid_opponent_ids = set()

    if club_a_id or club_b_id:
        if not club_a_id or not club_b_id:
            head_to_head_error = "Please select both teams."
        elif club_a_id == club_b_id:
            head_to_head_error = "You cannot compare the same club."
        elif not valid_opponent_ids:
            head_to_head_error = "No recorded opponents for Team A."
        elif club_b_id not in valid_opponent_ids:
            head_to_head_error = "Team B must be a club that has played against Team A."
        else:
            stats, matches = database.get_head_to_head(club_a_id, club_b_id, limit=5)
            head_to_head_stats = stats
            head_to_head_matches = matches
            if not stats:
                head_to_head_error = "No matches found between these clubs."

    total_pages = 0
    if total_results:
        total_pages = (total_results + per_page - 1) // per_page

    return render_template(
        'games.html',
        years=years,
        selected_year=selected_year,
        games=games,
        favorite_only=favorite_only,
        sort_option=sort_option,
        year_summary=year_summary,
        page=page,
        total_pages=total_pages,
        total_results=total_results,
        per_page=per_page,
        club_options=club_options,
        club_a_id=club_a_id,
        club_b_id=club_b_id,
        head_to_head_stats=head_to_head_stats,
        head_to_head_matches=head_to_head_matches,
        head_to_head_error=head_to_head_error,
        club_name_map=club_name_map,
        opponent_options=opponent_options,
        competition_options=competition_options,
    )

def get_opponents_for_club_api(club_id: int):
    """Return opponents for a given club as JSON."""
    opponents = database.get_opponents_for_club(club_id)
    return jsonify({"opponents": opponents or []})

def update_game_favorite(game_id: int):
    """Bir maçı favori olarak işaretler."""
    success = database.set_game_favorite(game_id, True)
    if not success:
        return jsonify({"success": False, "message": "Güncelleme yapılamadı."}), 500
    return jsonify({"success": True, "is_favorite": True})

def update_transfer(transfer_id: int):
    """Transfer kaydını günceller."""
    payload = request.get_json(silent=True) or {}

    def _parse_int(val, field):
        if val in (None, ""):
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid {field}.")

    try:
        parsed = {
            "from_club_id": _parse_int(payload.get("from_club_id"), "from club"),
            "to_club_id": _parse_int(payload.get("to_club_id"), "to club"),
            "transfer_fee": _parse_int(payload.get("transfer_fee"), "transfer fee"),
            "market_value_in_eur": _parse_int(payload.get("market_value_in_eur"), "market value"),
        }
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

    success = database.update_transfer(transfer_id, parsed)
    if not success:
        return jsonify({"success": False, "message": "Update failed."}), 500
    return jsonify({"success": True})


def delete_transfer(transfer_id: int):
    """Transfer kaydını siler."""
    deleted = database.delete_transfer(transfer_id)
    if not deleted:
        return jsonify({"success": False, "message": "Delete failed."}), 404
    return jsonify({"success": True})


def update_game(game_id: int):
    """Maç verisini günceller."""
    payload = request.get_json(silent=True) or {}

    def _parse_int(val, field):
        if val in (None, ""):
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid {field}.")

    def _parse_date(val):
        if val in (None, ""):
            return None
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            raise ValueError("Invalid date format.")

    try:
        parsed = {
            "home_club_id": _parse_int(payload.get("home_club_id"), "home club"),
            "away_club_id": _parse_int(payload.get("away_club_id"), "away club"),
            "competition_id": (payload.get("competition_id") or None),
            "home_club_goals": _parse_int(payload.get("home_club_goals"), "home goals"),
            "away_club_goals": _parse_int(payload.get("away_club_goals"), "away goals"),
            "date": _parse_date(payload.get("date")),
            "home_club_position": _parse_int(payload.get("home_club_position"), "home position"),
            "away_club_position": _parse_int(payload.get("away_club_position"), "away position"),
            "season": (payload.get("season") or None),
            "is_favorite": bool(payload.get("is_favorite")),
        }
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

    success = database.update_game(game_id, parsed)
    if not success:
        return jsonify({"success": False, "message": "Update failed."}), 500
    return jsonify({"success": True})


def delete_game(game_id: int):
    """Maç kaydını siler."""
    deleted = database.delete_game(game_id)
    if not deleted:
        return jsonify({"success": False, "message": "Delete failed."}), 404
    return jsonify({"success": True})

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

def competition_clubs_api(competition_id: str):
    """Belirli bir ligdeki kulüpleri JSON olarak döner."""
    clubs = database.get_clubs_by_competition(competition_id)
    return jsonify({"clubs": clubs or []})

def admin_page():
    admin_password = "1923"
    submitted_password = (request.form.get("admin_password") or "").strip()
    admin_authenticated = submitted_password == admin_password if submitted_password else False

    if request.method == "POST" and not admin_authenticated:
        return render_template(
            'admin.html',
            admin_authenticated=False,
            login_error="Wrong password. Please try again.",
        )

    if not admin_authenticated:
        return render_template(
            'admin.html',
            admin_authenticated=False,
            login_error=None,
        )

    tables = database.get_table_schemas()
    message = None
    error = None

    if request.method == "POST" and request.form.get("table_name"):
        table_name = (request.form.get("table_name") or "").strip()
        target_table = next((t for t in tables if t["name"] == table_name), None)
        if not target_table:
            error = "Select a valid table."
        else:
            row_data = {}
            for col in target_table["columns"]:
                val = request.form.get(col["name"])
                if val is not None and val != "":
                    row_data[col["name"]] = val

            if not row_data:
                error = "Provide at least one column value to insert."
            else:
                inserted = database.insert_row(table_name, row_data)
                if inserted:
                    message = f"Inserted row into {table_name}."
                else:
                    error = "Insert failed. Check required fields and values."

    return render_template(
        'admin.html',
        admin_authenticated=True,
        admin_password=admin_password,
        tables=tables,
        message=message,
        error=error,
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


def club_players_api(club_id: int):
    """Secilen kulup icin oyuncu listesini JSON olarak doner."""
    players = database.get_players_by_club(club_id)
    return jsonify({"players": players, "count": len(players)})
