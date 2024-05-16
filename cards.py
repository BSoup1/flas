# cards.py
# Define your database models using SQLAlchemy ORM, one file per each table

from app import db

class Card(db.Model):
    card_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'))
    card_content = db.Column(db.Text, nullable=False)
    translation = db.relationship('Translation', backref='card', uselist=False, cascade='all, delete-orphan')

    __tablename__ = 'cards'
