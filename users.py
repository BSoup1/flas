# users.py
# Definition of database models using SQLAlchemy ORM, one file per each table

from app import db
class User(db.Model):
    # __tablename__ attribute is set to "users", thus specifying the name of the table to ensure correct connection
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(60), unique=True, nullable=False) # corrected the value in the db
    password = db.Column(db.String(60), nullable=False)
