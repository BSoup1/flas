# translations.py
# Define your database models using SQLAlchemy ORM, one file per each table

from app import db

class Translation(db.Model):
    translation_id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.card_id', ondelete='CASCADE'), unique=True)
    translation_content = db.Column(db.Text, nullable=False)

    __tablename__ = 'translations'
