import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone
from extensions import db

class User(db.Model):
    """
    Represents a user in the database.
    Stores email, hashed password, and relation to resume analyses.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    analyses = db.relationship('ResumeAnalysis', backref='user', lazy=True)

class ResumeAnalysis(db.Model):
    """
    Represents a single evaluated resume document in the database.
    Stores the original filename, parsed text contents, and structured 
    Gemini JSON response for historical lookups and dashboard rendering.
    """
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    analysis_result = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
