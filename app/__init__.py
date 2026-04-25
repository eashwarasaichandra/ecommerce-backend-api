import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.exceptions import HTTPException

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_class='app.config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)

    # ── Register Blueprints ────────────────────────────────────────────
    from app.routes.auth_routes import auth_bp
    from app.routes.product_routes import product_bp
    from app.routes.cart_routes import cart_bp
    from app.routes.order_routes import order_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.ui_routes import ui_bp

    app.register_blueprint(auth_bp,    url_prefix='/api/auth')
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(cart_bp,    url_prefix='/api/cart')
    app.register_blueprint(order_bp,   url_prefix='/api/orders')
    app.register_blueprint(admin_bp,   url_prefix='/api/admin')
    app.register_blueprint(ui_bp)

    # ── Global Error Handlers ─────────────────────────────────────────

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad Request', 'message': str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication is required.'}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden', 'message': 'You do not have permission.'}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not Found', 'message': str(e)}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Method Not Allowed', 'message': str(e)}), 405

    @app.errorhandler(409)
    def conflict(e):
        return jsonify({'error': 'Conflict', 'message': str(e)}), 409

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()  # prevent broken sessions
        logger.error(f'Internal Server Error: {e}', exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'Something went wrong on our end.'}), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Catch-all: convert unhandled exceptions to JSON responses."""
        if isinstance(e, HTTPException):
            return jsonify({'error': e.name, 'message': e.description}), e.code
        db.session.rollback()
        logger.error(f'Unhandled Exception: {e}', exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred.'}), 500

    return app
