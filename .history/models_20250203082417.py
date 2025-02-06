from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    images = db.relationship('Image', backref='page', lazy=True, cascade="all, delete-orphan")

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=False)  # Store the binary image data
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)
