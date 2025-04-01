from flask import Flask, request, jsonify
from db import db, Player, Admin, Game, Cricket, get_player_by_email, create_player, authenticate_player

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5433/TrumpCards'

app.secret_key = "supersecretkey123"  
db.init_app(app)

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
    print(player)
    return jsonify({'message': 'Registration successful! You can now log in.'}), 201

@app.route('/login', methods=['POST'])
def login():
    print("login")
    data = request.get_json() 
    print(data)
    
    email = data.get('email')
    password = data.get('password') or data.get('pwd')

    player = authenticate_player(email, password)
    if player:
        return jsonify({'message': 'Login successful!', 'email': email, 'name': player.name}), 200
    else:
        return jsonify({'message': 'Invalid credentials, please try again.'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

