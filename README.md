# Digital Wardrobe

A full-stack Flask web app to digitize and manage your wardrobe.

## Features
- User authentication (register, login, logout)
- Add, edit, and delete clothing items
- Filter by type, color, size, material, and season
- Mark items as favorites
- Upload front and tag photos per item (stored on Cloudinary)

## Tech Stack
- Python / Flask
- SQLAlchemy + SQLite
- Cloudinary (image storage)
- Bootstrap 5
- Jinja2 templates

## Setup
1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with:
```
SECRET_KEY=your_secret_key
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```
4. Run: `python3 run.py`

## Contributors
 (Person A) — Authentication, add/edit/delete
 (Person B) — Dashboard filtering, favorites, image upload