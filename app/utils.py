import re
from functools import wraps
from flask import request, jsonify, current_app
import jwt
from app.models import User

# ---------------------------------------------------------------------------
# JWT Middleware
# ---------------------------------------------------------------------------

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            # Expected format: Bearer <token>
            auth_header = request.headers['Authorization']
            parts = auth_header.split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
            else:
                token = auth_header  # fallback just in case

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'User associated with token not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired! Please log in again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'message': 'Admin privileges required!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Input Validation Helpers
# ---------------------------------------------------------------------------

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


def validate_email(email: str) -> bool:
    """Return True if email matches a basic valid pattern."""
    return bool(EMAIL_REGEX.match(email)) if email else False


def validate_price(price) -> bool:
    """Return True if price is a positive number."""
    try:
        return float(price) > 0
    except (TypeError, ValueError):
        return False


def validate_stock(stock) -> bool:
    """Return True if stock is a non-negative integer."""
    try:
        return int(stock) >= 0
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Valid order status transitions (business logic)
# ---------------------------------------------------------------------------

VALID_ORDER_STATUSES = {'pending', 'shipped', 'delivered', 'cancelled'}

ORDER_STATUS_TRANSITIONS = {
    'pending':   {'shipped', 'cancelled'},
    'shipped':   {'delivered', 'cancelled'},
    'delivered': set(),   # terminal state
    'cancelled': set(),   # terminal state
}


def is_valid_status_transition(current_status: str, new_status: str) -> bool:
    """Return True if the transition from current_status to new_status is allowed."""
    allowed = ORDER_STATUS_TRANSITIONS.get(current_status, set())
    return new_status in allowed
