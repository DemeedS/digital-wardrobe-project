# digital-wardrobe-project

Digital Wardrobe — a small Flask web app to organize, filter and manage wardrobe items.

What it does
- Register and log in users
- Add, edit and delete wardrobe items (with simple attributes)
- Mark items as favorites and filter/search items from a dashboard

Prerequisites
- Python 3.10 or newer
- Git (optional)

Install
1. Create and activate a virtual environment:

	 python -m venv .venv
	 source .venv/bin/activate

2. Install dependencies:

	 pip install -r requirements.txt

Configuration
- The app loads settings from `config.Config` in `config.py`.
- Optional environment variables:
	- `SECRET_KEY` — override the default secret key (recommended in production)

Database
- Uses SQLite by default, configured as `sqlite:///wardrobe.db` in `config.py`.
- The database and tables are created automatically on first run.

Run
- Start the development server:

	python run.py

	The app will listen on http://127.0.0.1:5000 by default.

Project layout (key files)
- `run.py` — application entrypoint
- `app/__init__.py` — Flask app factory and extension setup
- `app/routes/` — blueprints: `auth.py` and `wardrobe.py`
- `app/models.py` and `models.py` — data models
- `templates/` and `static/` — UI and assets

Notes
- This project is intended for development and learning. Do not use the default `SECRET_KEY` in production.
- To deploy, set appropriate production configuration (secure secret, production-ready server, and database).

License
- See project root for licensing details (if any).

