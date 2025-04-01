import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from db import db, Player, Admin, Game, Cricket, get_player_by_email, create_player, authenticate_player, add_game, update_game_result, get_all_cricket_cards, add_cricket_card, update_cricket_card, delete_cricket_card

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5433/TrumpCards'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif','avif'}
app.secret_key = "supersecretkey123"

db.init_app(app)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.pwd == password:  
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials, please try again.", "danger")
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    cards = get_all_cricket_cards()  
    return render_template('dashboard.html', cards=cards)

@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if request.method == 'POST':
        name = request.form['name']
        power = request.form['power']
        strike_rate = request.form['strike_rate']
        img = None

        if 'img' in request.files:
            file = request.files['img']
            if file and allowed_file(file.filename):
                img_filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
                img = os.path.join('uploads', img_filename)  
        
        new_card = add_cricket_card(name, power, strike_rate, img=img)
        flash("Card added successfully!", "success")
        return redirect(url_for('dashboard'))
    
    return render_template('add_card.html')

@app.route('/edit_card/<int:card_id>', methods=['GET', 'POST'])
def edit_card(card_id):
    card = Cricket.query.get_or_404(card_id)

    if request.method == 'POST':
        card.player_name = request.form['player_name']
        card.power = int(request.form['power'])
        card.strike_rate = float(request.form['strike_rate'])
        card.wickets = int(request.form['wickets'])
        card.matches_played = int(request.form['matches_played'])
        card.runs_scored = int(request.form['runs_scored'])
        card.highest_score = int(request.form['highest_score'])
        
        if 'img' in request.files:
            file = request.files['img']
            if file and allowed_file(file.filename):
                img_filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
                card.img = os.path.join('uploads', img_filename)  
        
        db.session.commit()
        flash('Card updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_card.html', card=card)

@app.route('/delete_card/<int:id>', methods=['POST'])
def delete_card(id):
    if delete_cricket_card(id):
        flash("Card deleted successfully!", "success")
    else:
        flash("Error deleting card.", "danger")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user', None)  
    return redirect(url_for('login'))  

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

