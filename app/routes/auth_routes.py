from flask import Blueprint, request, jsonify, current_app
from app.models import User
from app import db, bcrypt
from app.utils import validate_email, validate_price
import jwt
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)


# -----------------------------------------------------------------------
# POST /api/auth/register
# -----------------------------------------------------------------------
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # ── Required field checks ──────────────────────────────────────────
    missing = [f for f in ('name', 'email', 'password') if not data or not data.get(f)]
    if missing:
        return jsonify({'message': f'Missing required fields: {", ".join(missing)}'}), 400

    # ── Email format validation ────────────────────────────────────────
    if not validate_email(data['email']):
        return jsonify({'message': 'Invalid email format. Please provide a valid email address.'}), 400

    # ── Password strength (min 6 chars) ───────────────────────────────
    if len(data['password']) < 6:
        return jsonify({'message': 'Password must be at least 6 characters.'}), 400

    # ── Duplicate check ───────────────────────────────────────────────
    if User.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'message': 'A user with this email already exists.'}), 409

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(
        name=data['name'].strip(),
        email=data['email'].lower().strip(),
        password_hash=hashed_password,
        role=data.get('role', 'user')  # allow setting admin for testing
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully!',
        'user': {
            'id': new_user.id,
            'name': new_user.name,
            'email': new_user.email,
            'role': new_user.role
        }
    }), 201


# -----------------------------------------------------------------------
# POST /api/auth/login
# -----------------------------------------------------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields: email, password'}), 400

    user = User.query.filter_by(email=data['email'].lower().strip()).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Invalid email or password.'}), 401

    expiry_hours = current_app.config.get('JWT_EXPIRATION_HOURS', 24)
    token = jwt.encode(
        {
            'user_id': user.id,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=expiry_hours)
        },
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )

    return jsonify({
        'message': 'Login successful!',
        'token': token,
        'expires_in': f'{expiry_hours}h',
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    }), 200


# -----------------------------------------------------------------------
# GET /api/auth/profile  — get own profile (token required)
# -----------------------------------------------------------------------
@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    from app.utils import token_required

    @token_required
    def _get(current_user):
        return jsonify({
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'role': current_user.role
        }), 200

    return _get()
