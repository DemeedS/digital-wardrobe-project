# Project Context — Digital Wardrobe

## What we're building
A full-stack Flask web app that digitizes a user's wardrobe. 
This is both a resume/GitHub project AND the foundation for a 
fashion-tech startup

## Current tech stack
- Python / Flask
- SQLAlchemy + SQLite
- Cloudinary (image storage)
- Bootstrap 5
- Jinja2 templates

## What's already built
- User authentication (register, login, logout) — built by (Person A)
- Dashboard with multi-filter (type, color, size, material, season) — built by (Person B)
- Favorites system (toggle + favorites page) — built by Person A
- Add, edit, delete clothing items
- Optional front + tag photo upload via Cloudinary

## Planned features (in priority order)
### Phase 2 — AI label reading
- "Add by photo" option on add item page
- User uploads front photo + tag photo
- Claude API reads the tag photo and auto-fills the form
  (color, material, size, brand)
- Form still shows pre-filled for user to review before saving

### Phase 3 — Visual enhancement
- Meta SAM background removal for clean product-style photos
- Eventually 3D avatar try-on (V2, post-validation)

## Startup vision
- Personal stylist + wardrobe manager + fashion discovery platform
- MVP: digital wardrobe + outfit recommendations based on calendar events
- Monetization: affiliate sales, brand promotions, premium subscription,
  anonymized data insights

## Key decisions already made
- Photos stored on Cloudinary (not local)
- Dashboard shows front photo thumbnail, tag accessible via modal click
- AI form fill shows pre-filled form for user to review (not auto-submit)
- Claude API for label reading (not OpenAI)
- Build features first, UI redesign last
- Deploy on Render when ready

## GitHub
- Repo: https://github.com/codepioneerr/digital-wardrobe-project
- Demian's branch: Person-B-Branch
- Nick's branch: Person-A-Branch
- Main is up to date