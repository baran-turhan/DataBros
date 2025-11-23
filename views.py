from datetime import datetime
from flask import render_template, request
import database

def base_page():
    return render_template('base.html')

def transfers_page():
    return render_template('transfers.html')

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
