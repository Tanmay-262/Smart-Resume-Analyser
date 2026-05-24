from app import app
from extensions import db
from sqlalchemy import text

with app.app_context():
    try:
        print("Running migration: ADD COLUMN user_id to resume_analysis...")
        with db.engine.begin() as conn:
            # We use IF NOT EXISTS for the column to be safe and rerun-proof
            conn.execute(text('ALTER TABLE resume_analysis ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES "user"(id);'))
        print("SUCCESS: Migration ran successfully!")
    except Exception as e:
        print("ERROR: Migration failed:", e)
