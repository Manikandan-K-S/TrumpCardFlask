from flask import Flask, request, jsonify
from db import (
    db, Player, Admin, Game, Cricket,
    get_player_by_email, create_player, authenticate_player,
    add_game
)
from GamePlay import GamePlay
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5433/TrumpCards'
app.secret_key = "supersecretkey123"
db.init_app(app)

# In-memory game state
onGoing = {}
waiting = None

##############################
#      Register/Login        #
##############################

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Invalid request!'}), 400

    email = data.get('email')
    name = data.get('name')
    password = data.get('password') or data.get('pwd')
    confirm_password = data.get('confirm_password') or data.get('pwd')

    if not email or not name or not password or not confirm_password:
        return jsonify({'message': 'All fields are required!'}), 400

    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match!'}), 400

    existing_player = get_player_by_email(email)
    if existing_player:
        return jsonify({'message': 'Email already exists!'}), 400

    player = create_player(email, name, password)
    return jsonify({'message': 'Registration successful! You can now log in.'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password') or data.get('pwd')

    player = authenticate_player(email, password)
    if player:
        return jsonify({'message': 'Login successful!', 'email': email, 'name': player.name}), 200
    else:
        return jsonify({'message': 'Invalid credentials, please try again.'}), 401

##############################
#     Game Matchmaking       #
##############################

@app.route('/start_game', methods=['POST'])
def start_game():
    global waiting
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required!'}), 400

    if waiting:
        player1 = waiting
        player2 = email
        game = add_game(player1, player2)

        all_cards = Cricket.query.all()
        random.shuffle(all_cards)
        mid = len(all_cards) // 2

        player1_cards = [card.id for card in all_cards[:mid]]
        player2_cards = [card.id for card in all_cards[mid:]]

        onGoing[game.id] = GamePlay(game.id, player1, player2, player1_cards, player2_cards)
        waiting = None

        return jsonify({'game_id': game.id, 'opponent': player1, 'match_found': True}), 200

    waiting = email
    return jsonify({'message': 'Waiting for an opponent...'}), 202

@app.route('/check_match', methods=['POST'])
def check_match():
    global waiting
    data = request.get_json()
    email = data.get('email')

    for game_id, game in onGoing.items():
        if email in [game.player1, game.player2]:
            opponent = game.player1 if game.player2 == email else game.player2
            return jsonify({'game_id': game_id, 'opponent': opponent, 'match_found': True}), 200

    if waiting == email:
        return jsonify({'message': 'Still waiting...'}), 202

    return jsonify({'message': 'Match not found, please restart matchmaking'}), 404

##############################
#     Turn & Game Flow       #
##############################

@app.route('/play_turn', methods=['POST'])
def play_turn():
    data = request.get_json()
    email = data.get('email')
    game_id = data.get('game_id')
    attribute = data.get('attribute')

    if not email or not game_id or not attribute:
        return jsonify({'message': 'Invalid request'}), 400

    game = onGoing.get(game_id)
    if not game:
        return jsonify({'message': 'Game not found'}), 404

    result = game.play_turn(email, attribute)

    if result.get('game_over'):
        del onGoing[game_id]

    return jsonify(result), 200

@app.route('/get_game_state', methods=['POST'])
def get_game_state():
    data = request.get_json()
    email = data.get('email')
    game_id = data.get('game_id')

    game = onGoing.get(game_id)
    if not game:
        return jsonify({'message': 'Game not found'}), 404

    return jsonify({
        'current_turn': game.get_current_turn(),
        'player_card': game.get_top_card(email),
        'opponent_card': game.get_top_card(game.player1 if game.player2 == email else game.player2)
    }), 200

@app.route('/leave_game', methods=['POST'])
def leave_game():
    global waiting
    data = request.get_json()
    email = data.get('email')

    if waiting == email:
        waiting = None
        return jsonify({'message': 'Left matchmaking'}), 200

    for game_id, game in list(onGoing.items()):
        if email in [game.player1, game.player2]:
            del onGoing[game_id]
            return jsonify({'message': 'Game exited'}), 200

    return jsonify({'message': 'No active game found'}), 404

##############################
#          Main              #
##############################

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
