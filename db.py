from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

# ---------------- Models ----------------

class Player(db.Model):
    __tablename__ = 'players'
    email = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    pwd = db.Column(db.Text, nullable=False)

class Admin(db.Model):
    __tablename__ = 'admin'
    email = db.Column(db.String(255), primary_key=True)
    pwd = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False)

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    player1 = db.Column(db.String(255), db.ForeignKey('players.email', ondelete="CASCADE"), nullable=False)
    player2 = db.Column(db.String(255), db.ForeignKey('players.email', ondelete="CASCADE"), nullable=True)
    winner = db.Column(db.String(255), db.ForeignKey('players.email', ondelete="SET NULL"), nullable=True)
    loser = db.Column(db.String(255), db.ForeignKey('players.email', ondelete="SET NULL"), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Cricket(db.Model):
    __tablename__ = 'cricket'
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(255), nullable=False)
    power = db.Column(db.Integer, nullable=False)
    strike_rate = db.Column(db.Float, nullable=False)
    wickets = db.Column(db.Integer, default=0)
    matches_played = db.Column(db.Integer, default=0)
    runs_scored = db.Column(db.Integer, default=0)
    highest_score = db.Column(db.Integer, default=0)
    img = db.Column(db.Text)  
    win_stats = db.Column(db.JSON, default={})  # Stores attribute win counts

# ---------------- Player Functions ----------------

def get_player_by_email(email):
    return Player.query.filter_by(email=email).first()

def create_player(email, name, pwd):
    hashed_pwd = generate_password_hash(pwd)
    player = Player(email=email, name=name, pwd=hashed_pwd)
    db.session.add(player)
    db.session.commit()
    return player

def authenticate_player(email, pwd):
    player = Player.query.filter_by(email=email).first()
    if player and check_password_hash(player.pwd, pwd):
        return player
    return None

# ---------------- Game Functions ----------------

def add_game(player1_email, player2_email=None):
    """Create a new game entry in the database."""
    game = Game(player1=player1_email, player2=player2_email)
    db.session.add(game)
    db.session.commit()
    return game

def get_game_by_id(game_id):
    """Retrieve a game by ID."""
    return Game.query.get(game_id)

def update_game_result(game_id, winner_email, loser_email):
    """Update the game with winner and loser details."""
    game = Game.query.get(game_id)
    if game:
        game.winner = winner_email
        game.loser = loser_email
        db.session.commit()
    return game

# ---------------- Cricket Card Functions ----------------

def get_all_cricket_cards():
    return Cricket.query.all()

def get_cricket_card_by_id(card_id):
    return Cricket.query.get(card_id)

def add_cricket_card(player_name, power, strike_rate, wickets=0, matches_played=0, runs_scored=0, highest_score=0, img=None):
    card = Cricket(
        player_name=player_name,
        power=power,
        strike_rate=strike_rate,
        wickets=wickets,
        matches_played=matches_played,
        runs_scored=runs_scored,
        highest_score=highest_score,
        img=img
    )
    db.session.add(card)
    db.session.commit()
    return card

def update_cricket_card(card_id, **kwargs):
    """Update cricket card attributes."""
    card = Cricket.query.get(card_id)
    if not card:
        return None

    for key, value in kwargs.items():
        if hasattr(card, key):
            setattr(card, key, value)
    db.session.commit()
    return card

def delete_cricket_card(card_id):
    """Delete a cricket card from the database."""
    card = Cricket.query.get(card_id)
    if card:
        db.session.delete(card)
        db.session.commit()
        return True
    return False

# ---------------- Win Stats Functions ----------------

def update_win_stats(card_id, attribute):
    """Increment the win count of a given attribute for a card."""
    card = Cricket.query.get(card_id)
    if not card:
        return None
    
    win_stats = card.win_stats or {}  # Ensure it's a dictionary
    win_stats[attribute] = win_stats.get(attribute, 0) + 1
    card.win_stats = win_stats

    db.session.commit()
    return card
