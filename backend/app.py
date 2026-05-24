import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import traceback

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import pdfplumber
    import docx
    import os
    from dotenv import load_dotenv
    import google.generativeai as genai
    from flask_sqlalchemy import SQLAlchemy
    from datetime import datetime, timezone
    import json
    from werkzeug.security import generate_password_hash, check_password_hash
    from auth import generate_token, token_required
except Exception as e:
    print("FATAL IMPORT ERROR IN app.py:", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    raise e

app = Flask(__name__)
CORS(app)
load_dotenv()

from extensions import db
from models import User, ResumeAnalysis

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create tables if they don't exist
with app.app_context():
    db.create_all()

def extract_text_from_pdf(file_path):
    """
    Opens a PDF document at file_path using pdfplumber, iterates 
    through all pages, and extracts continuous plain text.
    """
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_path):
    """
    Opens a DOCX document at file_path using python-docx and extracts 
    continuous plain text from all paragraphs.
    """
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

@app.route('/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        if not data or not data.get('name') or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Missing required fields"}), 400
            
        name = data.get('name').strip()
        email = data.get('email').strip().lower()
        password = data.get('password')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "User with this email already exists"}), 409
            
        # Hash password and save
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Automatically generate token for signup
        token = generate_token(new_user.id)
        
        return jsonify({
            "message": "User registered successfully",
            "token": token,
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email
            }
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Missing required fields"}), 400
            
        email = data.get('email').strip().lower()
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid email or password"}), 401
            
        token = generate_token(user.id)
        
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
@token_required
def analyze_resume(current_user):
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        file_path = os.path.join("uploads", file.filename)
        os.makedirs("uploads", exist_ok=True)
        file.save(file_path)

        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif file.filename.endswith('.docx'):
            text = extract_text_from_docx(file_path)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        # Configure model to force JSON output
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )

        prompt = f"""
        You are an expert AI resume evaluator and career co-pilot.
        Analyze the following resume text and provide a highly objective, professional assessment.
        
        Evaluate the quality of the resume on a scale of 0.0 to 10.0, where:
        - 9.0 to 10.0: Outstanding resume, minimal changes needed.
        - 7.5 to 8.9: Strong resume, minor improvements suggested.
        - 5.0 to 7.4: Average resume, significant layout or content adjustments needed.
        - 0.0 to 4.9: Weak resume, major rewrite needed.
        
        Calculate a unique, highly objective overall_score based ONLY on the quality of the uploaded resume text. Do NOT default to any template scores.

        You MUST return your response as a valid JSON object matching the following structure:
        {{
          "candidate_name": "Full name of the candidate extracted from the resume. If not found, use 'Guest User'",
          "candidate_email": "Email address of the candidate extracted from the resume. If not found, use 'guest@example.com'",
          "headline": "A short, positive rating headline based on your actual computed score (e.g., 'Great Job! 🎉', 'Impressive Draft! 🚀', 'Solid Foundation! 👍', 'Needs Improvements! ⚠️')",
          "summary": "A concise, 3-4 sentence professional summary of the candidate's background and expertise.",
          "strengths": [
            "Provide a clear strength and how it appears in the resume"
          ],
          "weaknesses": [
            "Detail a critical missing skill or area that can be improved"
          ],
          "suggested_roles": [
            "Job Title 1",
            "Job Title 2"
          ],
          "recommendations": [
            "Provide an actionable recommendation with numbers/impact",
            "Provide a layout or formatting recommendation",
            "Provide a specific skill to showcase",
            "Provide a recommendation about links (GitHub, LinkedIn) or achievements"
          ],
          "overall_score": 0.0
        }}

        IMPORTANT: For "overall_score", replace the placeholder 0.0 with your actual computed float or integer score between 0.0 and 10.0 (e.g., 6.4, 7.8, 9.2) representing the true quality of the resume. Do NOT output 0.0 or 8.6 unless it is the actual calculated score.
        Please provide exactly 4 strengths, 4 weaknesses, 4 suggested roles, and 4 recommendations.

        Resume Text:
        {text}
        """

        response = model.generate_content(prompt)

        # Save to database
        new_analysis = ResumeAnalysis(
            filename=file.filename,
            raw_text=text,
            analysis_result=response.text,
            user_id=current_user.id
        )
        db.session.add(new_analysis)
        db.session.commit()

        return jsonify({
            "id": new_analysis.id,
            "resume_analysis": json.loads(response.text)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyses', methods=['GET'])
@token_required
def get_analyses(current_user):
    try:
        analyses = ResumeAnalysis.query.filter_by(user_id=current_user.id).order_by(ResumeAnalysis.created_at.desc()).all()
        result = []
        for a in analyses:
            score = None
            name = "Guest User"
            email = "guest@example.com"
            try:
                data = json.loads(a.analysis_result)
                score = data.get("overall_score")
                name = data.get("candidate_name", "Guest User")
                email = data.get("candidate_email", "guest@example.com")
            except Exception:
                # Graceful fallback for old text-based records
                pass
            result.append({
                "id": a.id,
                "filename": a.filename,
                "created_at": a.created_at.isoformat(),
                "overall_score": score,
                "candidate_name": name,
                "candidate_email": email
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyses/<int:analysis_id>', methods=['GET'])
@token_required
def get_analysis_detail(current_user, analysis_id):
    try:
        analysis = ResumeAnalysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()
        if not analysis:
            return jsonify({"error": "Analysis not found"}), 404
            
        result_data = analysis.analysis_result
        try:
            result_data = json.loads(analysis.analysis_result)
        except Exception:
            pass
            
        return jsonify({
            "id": analysis.id,
            "filename": analysis.filename,
            "raw_text": analysis.raw_text,
            "analysis_result": result_data,
            "created_at": analysis.created_at.isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
