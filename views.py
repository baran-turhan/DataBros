from flask import render_template, current_app
import database

def base_page():
    return render_template('base.html')

def transfers_page():
    return render_template('transfers.html')

def players_page():
    return render_template('players.html')

def games_page():
    return render_template('games.html')

def competitions_page():
    return render_template('competitions.html')

def clubs_page():
    """Kulüpler sayfasını render eder ve veritabanından kulüp verilerini çeker."""
    clubs = database.get_all_clubs()
    return render_template('clubs.html', clubs=clubs)