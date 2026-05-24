import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify

def generate_token(user_id):
    """
    Generates a secure JSON Web Token (JWT) for a specific user ID.
    The token includes standard claims: exp (expiration in 24 hours),
    iat (issued at time), and sub (subject user ID).
    """
    try:
        payload = {
            'exp': datetime.now(timezone.utc) + timedelta(days=1),
            'iat': datetime.now(timezone.utc),
            'sub': str(user_id)
        }
        secret = os.getenv("JWT_SECRET_KEY", "default-fallback-super-secret-key-12345")
        return jwt.encode(payload, secret, algorithm='HS256')
    except Exception as e:
        return None

def token_required(f):
    """
    A custom Flask route decorator to authenticate requests.
    Validates that a valid Bearer JWT is passed in the Authorization header.
    Passes the authenticated User object to the decorated route.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        
        try:
            secret = os.getenv("JWT_SECRET_KEY", "default-fallback-super-secret-key-12345")
            data = jwt.decode(token, secret, algorithms=['HS256'])
            
            # Import from models to avoid circular dependencies with app
            from models import User
            current_user = User.query.filter_by(id=int(data['sub'])).first()
            if not current_user:
                return jsonify({'error': 'User not found!'}), 401
                
        except jwt.ExpiredSignatureError as e:
            print("JWT Expired Signature Error:", e)
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError as e:
            print("JWT Invalid Token Error:", e)
            return jsonify({'error': 'Invalid token!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated
