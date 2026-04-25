from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file

from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create all tables on startup if they don't exist
        db.create_all()
    app.run(debug=True, port=5000)
