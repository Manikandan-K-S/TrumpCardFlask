from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

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
    game = Game(player1=player1_email, player2=player2_email)
    db.session.add(game)
    db.session.commit()
    return game

def get_game_by_id(game_id):
    return Game.query.get(game_id)

def update_game_result(game_id, winner_email, loser_email):
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
    card = Cricket.query.get(card_id)
    if not card:
        return None
    for key, value in kwargs.items():
        if hasattr(card, key):
            setattr(card, key, value)
    db.session.commit()
    return card

def delete_cricket_card(card_id):
    card = Cricket.query.get(card_id)
    if card:
        db.session.delete(card)
        db.session.commit()
        return True
    return False


def get_player_match_history(email):
    # Fetch games where the player is either player1 or player2
    games = Game.query.filter(
        (Game.player1 == email) | (Game.player2 == email)
    ).order_by(Game.timestamp.desc()).all()

    history = []
    for game in games:
        if game.player1 == email:
            opponent_email = game.player2
        else:
            opponent_email = game.player1

        # Fetch opponent name if email is present
        opponent_name = None
        if opponent_email:
            opponent = Player.query.filter_by(email=opponent_email).first()
            opponent_name = opponent.name if opponent else "Unknown"

        # Determine result
        if game.winner == email:
            result = "Win"
        elif game.loser == email:
            result = "Lose"
        else:
            result = "Draw"

        history.append({
            "game_id": game.id,
            "opponent": opponent_name,
            "result": result,
            "timestamp": game.timestamp
        })

    print("Match history for player {}: {}".format(email, history))
    return history
