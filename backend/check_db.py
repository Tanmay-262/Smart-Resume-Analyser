import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app
from extensions import db
from models import ResumeAnalysis

with app.app_context():
    analyses = ResumeAnalysis.query.all()
    print(f"Total records in DB: {len(analyses)}")
    for a in analyses:
        print("-" * 40)
        print(f"ID: {a.id}")
        print(f"Filename: {a.filename}")
        print(f"Created At: {a.created_at}")
        print(f"Raw Text snippet: {a.raw_text[:100]}...")
        print(f"Analysis Result snippet: {a.analysis_result[:100]}...")
