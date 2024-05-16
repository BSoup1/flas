# Import necessary modules and initialize Flask app
import os
import sqlalchemy as sa
from flask import Flask, flash, render_template, url_for, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect, CSRFError
# Import the load_dotenv function from the dotenv module
from dotenv import load_dotenv

# Load environment variables from the .env file into the current environment
#This is necassary for hiding a password to the database in the env variable
load_dotenv()

# Create a Flask application instance
app = Flask(__name__)

# Retrieve the PostgreSQL password from the environment variable
postgres_password = os.getenv('PG_PASSWORD')

# Configure SQLAlchemy database URI and track modifications
# commented out URI for connecting to a local db on my pc
#app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:{postgres_password}@localhost/flashcards'
# Configure SQLAlchemy database URI and track modifications
# Use the internal hostname or IP address provided by Render
# GENERAL FORM >>> app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:' + postgres_password + '@<internal-hostname>:<port>/flashcards'
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:{postgres_password}@dpg-cp2uddkf7o1s73bnvcgg-a:5432/flashcards'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set a secret key for session security
app.secret_key = 'your_secret_key'
app.config['WTF_CSRF_ENABLED'] = False  # Enables or disables CSRF protection

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Initialize SQLAlchemy and Migrate for database operations
db = SQLAlchemy(app)
# migrate = Migrate(app, db)   #disabled code for database migration

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Check if the database needs to be initialized
engine = sa.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
inspector = sa.inspect(engine)
if not inspector.has_table("users"):
    with app.app_context():
        db.drop_all()
        db.create_all()
        app.logger.info('Initialized the database!')
else:
    app.logger.info('Database already contains the users table.')
 

# Import database models defined in seperate files
from users import User
from cards import Card
from translations import Translation

# Check database connection route
@app.route("/check_connection")
def check_connection():
    try:
        db.session.query(User).first()  # Test the database connection by querying the User table
        return "Database connection is working!"
    except Exception as e:
        return f"Error: {str(e)}"

# Home route
@app.route("/")
def index():
    # Check if the user is logged in
    if 'user_id' in session:
        # Get flash message and category from the query parameters
        message = request.args.get('message')
        category = request.args.get('category')
        user_id = session['user_id']
        # Query cards associated with the logged-in user
        user_cards = Card.query.filter_by(user_id=user_id).all()
        return render_template("home.html", message=message, category=category, user_cards=user_cards)
    else:
        # Redirect to the login page if the user is not logged in
        flash("You need to log in first.", "warning")
        return redirect(url_for("login"))

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Extract email and password from the login form
        email = request.form['email']
        password = request.form['password']

        # Check if the user exists in the database
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            # Set session variable to indicate user is logged in
            session['user_id'] = user.user_id
            # Flash success message and redirect to the home page
            flash("You have logged in!", "success")
            return redirect(url_for("index", message="You have logged in!", category="success"))
        else:
            # Flash error message if the user does not exist or the password is incorrect
            flash("The user does not exist or the password is incorrect. Please try again.", "danger")

    return render_template("login.html")

# Logout route
@app.route("/logout")
def logout():
    # Remove user_id from session to log out user
    session.pop('user_id', None)
    # Remove flash message related to login
    session.pop('_flashes', None)
    return redirect(url_for("login"))

# Register route
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        # Extract email and password from the registration form
        email = request.form['email']
        password = request.form['password']

        # Check if the user already exists in the database
        existing_user = User.query.filter_by(email=email).first()

        # If the user doesn't exist, create a new user
        if not existing_user:
            # Hash the password before storing it in the database
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            # Create a new User object and add it to the database session
            new_user = User(email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            # Log in the user
            session['user_id'] = new_user.user_id
            # Flash success message and redirect to the home page
            flash("User registered successfully!", "success")
            return redirect(url_for("index", message="You have registered successfully!", category="success"))
        else:
            # Flash error message if the user already exists
            flash("User already exists. Please choose a different email or login.", "danger")

    return render_template("register.html")

# Route for adding a new card via AJAX
# Route for adding a new card via AJAX
@app.route("/add_card", methods=["POST"])
def add_card():
    if 'user_id' in session:
        user_id = session['user_id']
        card_content = request.json.get('card_content')
        translation = request.json.get('translation')
        
        # Create a new card object and add it to the database session
        new_card = Card(user_id=user_id, card_content=card_content)
        db.session.add(new_card)
        
        # Commit the changes to the database
        db.session.commit()
        
         # Get the ID of the newly added card
        new_card_id = new_card.card_id
        
        # Create a new translation object and associate it with the new card
        new_translation = Translation(card_id=new_card.card_id, translation_content=translation)
        db.session.add(new_translation)
        
        # Commit the changes to the database
        db.session.commit()
        
        return jsonify({"message": "Card added successfully!", "category": "success", "card_id": new_card_id})
    else:
        return jsonify({"message": "You need to log in first.", "category": "warning"})

# Route for retrieving user-specific cards
@app.route("/get_user_cards", methods=["GET"])
def get_user_cards():
    if 'user_id' in session:
        user_id = session['user_id']
        
        # Query cards associated with the logged-in user
        user_cards = Card.query.filter_by(user_id=user_id).all()
        
        # Prepare JSON response with card data
        cards_data = []
        for card in user_cards:
            cards_data.append({
                "card_id": card.card_id,
                "card_content": card.card_content,
                "translation": card.translation.translation_content if card.translation else ""
            })
        
        return jsonify(cards_data)
    else:
        return jsonify({"message": "You need to log in first.", "category": "warning"})

# Route for updating a card via AJAX
@app.route("/update_card/<int:card_id>", methods=["POST"])
def update_card(card_id):
    if 'user_id' in session:
        user_id = session['user_id']
        new_card_content = request.json.get('card_content')
        
        # Update the card only if it belongs to the logged-in user
        card = Card.query.filter_by(card_id=card_id, user_id=user_id).first()
        if card:
            card.card_content = new_card_content
            db.session.commit()
            return jsonify({"message": "Card updated successfully!", "category": "success", "card_id": card_id})
        else:
            return jsonify({"message": "You are not authorized to update this card.", "category": "danger"})
    else:
        return jsonify({"message": "You need to log in first.", "category": "warning"})


# Route for deleting a card via AJAX
@app.route("/delete_card/<int:card_id>", methods=["POST"])
def delete_card(card_id):
    if 'user_id' in session:
        user_id = session['user_id']
        
        # Delete the card only if it belongs to the logged-in user
        card = Card.query.filter_by(card_id=card_id, user_id=user_id).first()
        if card:
            db.session.delete(card)
            db.session.commit()
            return jsonify({"message": "Card deleted successfully!", "category": "success"})
        else:
            return jsonify({"message": "You are not authorized to delete this card.", "category": "danger"})
    else:
        return jsonify({"message": "You need to log in first.", "category": "warning"})

# Run the Flask app with logging activity in Gunicorn Production Server
# Check if the script is being run directly (not imported as a module)
if __name__ == "__main__":
    # Import necessary modules
    import logging
    from gunicorn import glogging

    # Define a custom logger class that inherits from Gunicorn's default logger class
    class CustomGunicornLogger(glogging.Logger):
        def setup(self, cfg):
            # Call the setup method of the parent class to inherit its behavior
            super().setup(cfg)
            # Add custom configurations if needed

    # Create an instance of the custom logger class
    gunicorn_logger = CustomGunicornLogger()

    # Set Flask's logger handlers to the handlers of the custom Gunicorn logger
    app.logger.handlers = gunicorn_logger.handlers

    # Set Flask's logger level to match the level of the custom Gunicorn logger
    app.logger.setLevel(gunicorn_logger.level)

    # Run the Flask app
    app.run()

