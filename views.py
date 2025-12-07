from flask import render_template, current_app
import utils.database as database

def base_page():
    return render_template('base.html')

def transfers_page():
    return render_template('transfers.html')

def players_page():
    players = database.get_all_players()
    return render_template('players.html', players=players)

def games_page():
    return render_template('games.html')

def competitions_page():
    """Mücadeleler sayfasını render eder ve veritabanından mücadele verilerini çeker."""
    competitions = database.get_all_competitions()
    return render_template('competitions.html', competitions=competitions)

def clubs_page():
    """Kulüpler sayfasını render eder ve veritabanından kulüp verilerini çeker."""
    clubs = database.get_all_clubs()
    return render_template('clubs.html', clubs=clubs)