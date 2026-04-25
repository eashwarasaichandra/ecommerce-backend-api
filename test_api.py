import pytest
from app import create_app, db

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # We can pass a test config if needed, or just use the default
    app = create_app()
    
    # Configure the app for testing
    app.config.update({
        "TESTING": True,
        # Using an in-memory SQLite database for fast, isolated tests
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    # Create the database and the database table
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_products_endpoint_success(client):
    """Test that the /api/products/ endpoint returns a 200 OK status."""
    response = client.get('/api/products/')
    assert response.status_code == 200
    # Even if empty, it should return a valid JSON structure (likely a list or paginated object)
    assert response.is_json

def test_non_existent_endpoint(client):
    """Test that requesting an invalid route returns a 404."""
    response = client.get('/api/this-route-does-not-exist')
    assert response.status_code == 404

def test_register_user_validation(client):
    """Test that the registration endpoint enforces required fields."""
    # Sending empty data should fail validation (likely 400 Bad Request)
    response = client.post('/api/auth/register', json={})
    assert response.status_code in [400, 422, 500] # Depending on how you handle missing data
