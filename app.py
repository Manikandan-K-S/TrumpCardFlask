from flask import Flask, request, jsonify
from flask_cors import CORS
import random
from flask import send_from_directory
import socket
from flask import send_file
from werkzeug.utils import safe_join
from werkzeug.exceptions import abort


from db import (
    db,
    get_player_by_email,
    create_player,
    authenticate_player,
    add_game,
    update_game_result,
    get_game_by_id,
    get_player_match_history,
    Cricket,
)
from gameplay import GamePlay

app = Flask(__name__)
CORS(app)

# ---- Config ----
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5433/TrumpCards'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db.init_app(app)

# ---- In-memory state ----
onGoing = {}    # maps game_id (str) -> GamePlay instance
waiting = None  # holds (game_id (str), email) tuple when one player is waiting

# -------- Register/Login --------

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    name = data.get('name')
    password = data.get('pwd')
    if not email or not name or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    if get_player_by_email(email):
        return jsonify({'error': 'Email already registered'}), 409
    create_player(email, name, password)
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    player = authenticate_player(data.get('email'), data.get('password'))
    if player:
        return jsonify({'message': 'Login successful', 'email': player.email, 'name': player.name}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# -------- Matchmaking --------

@app.route('/start_game', methods=['POST'])
def start_game():
    global waiting
    data = request.get_json() or {}
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email required'}), 400

    # if the same user polls twice, still waiting
    if waiting and waiting[1] == email:
        gp = onGoing.get(waiting[0])
        if gp and not gp.matched:
            return jsonify({'game_id': waiting[0], 'message': 'waiting'}), 202

    if waiting is None:
        # first player
        g = add_game(email)
        waiting = (str(g.id), email)
        gp = GamePlay(str(g.id), email)
        onGoing[str(g.id)] = gp
        return jsonify({'game_id': g.id, 'message': 'waiting'}), 202

    # second player joins
    game_id, opponent_email = waiting
    gp = onGoing.get(game_id)
    gp.player2 = email
    gp.matched = True
    gp.join(email)
    # persist player2 in DB
    from db import Game
    game = Game.query.get(int(game_id))
    game.player2 = email
    db.session.commit()

    waiting = None
    return jsonify({'game_id': game_id, 'opponent': opponent_email, 'message': 'matched'}), 200

@app.route('/check_match', methods=['POST'])
def check_match():
    data = request.get_json() or {}
    game_id = str(data.get('game_id'))
    if not game_id:
        return jsonify({'error': 'Game ID is required'}), 400
    gp = onGoing.get(game_id)
    if not gp:
        return jsonify({'error': 'Game not found'}), 404
    if gp.matched:
        return jsonify({'game_id': game_id, 'message': 'matched'}), 200
    return jsonify({'message': 'waiting'}), 202

# -------- Gameplay --------

@app.route('/get_game_state', methods=['POST'])
def get_game_state():
    data = request.get_json() or {}
    gid = str(data.get('game_id'))
    email = data.get('email')
    gp = onGoing.get(gid)
    if not gp:
        return jsonify({'error': 'Game not found'}), 404

    your_card = gp.get_top_card(email)

    if your_card and 'img' in your_card:
        img_path = your_card['img'].replace('\\', '/')
        ip_address = socket.gethostbyname(socket.gethostname())
        if not your_card['img'].startswith('http://'):
            your_card['img'] = f"http://{ip_address}:5000/{img_path}"
    

    return jsonify({
        'turn': gp.get_current_turn(),
        'your_card': your_card
    }), 200

# 1) Modify /play_turn to only acknowledge receipt
@app.route('/play_turn', methods=['POST'])
def play_turn():
    data = request.get_json() or {}
    gid   = str(data.get('game_id'))
    email = data.get('email')
    attr  = data.get('attribute')
    gp    = onGoing.get(gid)
    if not gp:
        return jsonify({'error': 'Game not found'}), 404

    # execute the turn logic (populates gp.last_result and gp.turn_processed)
    gp.play_turn(email, attr)

    # only send back a boolean flag
    return jsonify({'processed': True}), 200


@app.route('/decide_starter', methods=['POST'])
def decide_starter():
    data = request.get_json() or {}
    game_id = str(data.get('game_id'))
    gp = onGoing.get(game_id)
    if not gp:
        return jsonify({'error': 'Invalid game ID'}), 404
    if gp.starter is None:
        gp.starter = random.choice([gp.player1, gp.player2])
        gp.turn = gp.starter
    return jsonify({'starter': gp.starter}), 200


@app.route('/get_turn_details', methods=['POST'])
def get_turn_details():
    data = request.get_json() or {}
    game_id = str(data.get('game_id'))
    email = data.get('email')
    gp = onGoing.get(game_id)

    if not gp:
        return jsonify({'error': 'Invalid game ID'}), 404
    if not email:
        return jsonify({'error': 'Email required'}), 400

    lr = gp.last_result or {}

    winner_email = lr.get('winner')
    won_card = lr.get('won_card')
    lost_card = lr.get('lost_card')
    attribute = lr.get('attribute')

    if not winner_email or not won_card or not lost_card or not attribute:
        return jsonify({'error': 'Turn result not available'}), 400

    if winner_email == email:
        # Winner sees the card they defeated (lost_card)
        message = f"You won this turn! Opponent's card had {attribute}: {lost_card.get(attribute)}"
        response = {
            'card': lost_card,
            'message': message,
            'attribute': attribute,
            'result': True,
            'gameOver': lr.get('gameOver'),
            'next_turn': lr.get('next_turn')
        }
    else:
        # Loser sees the card they lost to (won_card)
        message = f"You lost this turn! Opponent's card had {attribute}: {won_card.get(attribute)}"
        response = {
            'card': won_card,
            'message': message,
            'attribute': attribute,
            'result': False,
            'gameOver': lr.get('gameOver'),
            'next_turn': lr.get('next_turn')
        }

    if lr.get('gameOver'):
        response['overallWinner'] = lr.get('overallWinner')

    return jsonify(response), 200



# -------- Lightweight endpoints for IdlePlayerActivity --------

# 2) Update /check_turn_processed to reset the flag when returning True
@app.route('/check_turn_processed', methods=['POST'])
def check_turn_processed():
    data    = request.get_json() or {}
    game_id = str(data.get('game_id'))
    gp      = onGoing.get(game_id)
    if not gp:
        return jsonify({'error': 'Invalid game ID'}), 404

    if gp.turn_processed:
        # consume the flag immediately so future polls wait
        gp.turn_processed = False
        return jsonify({'turn_processed': True}), 200

    return jsonify({'turn_processed': False}), 200


@app.route('/get_match_history', methods=['POST'])
def get_match_history():
    data    = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    # Fetch the match history for the player
    history = get_player_match_history(email)
    
    return jsonify({"history": history})


@app.route('/reset_turn', methods=['POST'])
def reset_turn():
    data = request.get_json() or {}
    game_id = str(data.get('game_id'))
    gp = onGoing.get(game_id)
    if not gp:
        return jsonify({'error': 'Invalid game ID'}), 404
    gp.turn_processed = False
    gp.last_result = None
    return jsonify({'message': 'Turn reset'}), 200

# -------- Cricket card CRUD --------

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    try:
        path = safe_join(app.static_folder, 'uploads', filename)
        return send_file(path, conditional=True)
    except FileNotFoundError:
        abort(404)



@app.route('/all_cards', methods=['GET'])
def get_all_cards():
    cards = Cricket.query.all()
    return jsonify([c.to_dict() for c in cards]), 200

@app.route('/card/<int:card_id>', methods=['GET'])
def get_card(card_id):
    c = Cricket.query.get(card_id)
    if not c:
        return jsonify({'error': 'Card not found'}), 404
    return jsonify(c.to_dict()), 200

@app.route('/card', methods=['POST'])
def add_card():
    data = request.get_json() or {}
    try:
        c = Cricket(**data)
        db.session.add(c)
        db.session.commit()
        return jsonify({'message': 'Card added'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/card/<int:card_id>', methods=['PUT'])
def update_card(card_id):
    data = request.get_json() or {}
    c = Cricket.query.get(card_id)
    if not c:
        return jsonify({'error': 'Card not found'}), 404
    for k, v in data.items():
        setattr(c, k, v)
    db.session.commit()
    return jsonify({'message': 'Card updated'}), 200

@app.route('/card/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    c = Cricket.query.get(card_id)
    if not c:
        return jsonify({'error': 'Card not found'}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': 'Card deleted'}), 200

# -------- Main --------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
