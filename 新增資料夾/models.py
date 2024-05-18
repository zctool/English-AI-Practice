from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Topic(db.Model):
    __tablename__ = 'topic'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)

class Vocabulary(db.Model):
    __tablename__ = 'vocabulary'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    vocabulary_en = db.Column(db.String(255), nullable=False)
    vocabulary_tw = db.Column(db.String(255), nullable=False)
    PartOfSpeech = db.Column(db.String(255), nullable=False)
    IPA = db.Column(db.String(255), nullable=True)
    example = db.Column(db.Text, nullable=True)
    vocabulary_voice = db.Column(db.String(255), nullable=True)

class VocabularyCollect(db.Model):
    __tablename__ = 'vocabularyCollect'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    collect = db.Column(db.String(255), nullable=False)
