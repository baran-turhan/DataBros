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
    """Renders the competitions page and fetches competition data from the database."""
    competitions = database.get_all_competitions()
    return render_template('competitions.html', competitions=competitions)

def clubs_page():
    """Renders the clubs page and fetches club data from the database."""
    clubs = database.get_all_clubs()
    return render_template('clubs.html', clubs=clubs)
