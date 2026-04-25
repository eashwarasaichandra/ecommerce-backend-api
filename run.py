from dotenv import load_dotenv
load_dotenv()  # Load .env for local development

from app import create_app, db

app = create_app()

# Create all DB tables at startup — works for both `python run.py` AND gunicorn
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
