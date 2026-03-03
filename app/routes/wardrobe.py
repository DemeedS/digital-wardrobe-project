# ============================================================
# WARDROBE ROUTES - all clothing item functionality
# Includes dashboard, add, edit, delete, favorites, and
# Cloudinary image upload for front and tag photos
# ============================================================

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models import ClothingItem
import cloudinary
import cloudinary.uploader
import anthropic
import base64
import json
from app.label_analyzer import analyze_label

wardrobe = Blueprint('wardrobe', __name__)

# ============================================================
# CLOUDINARY SETUP - configure using credentials from config
# ============================================================
def configure_cloudinary():
    cloudinary.config(
        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=current_app.config['CLOUDINARY_API_KEY'],
        api_secret=current_app.config['CLOUDINARY_API_SECRET']
    )

# ============================================================
# HELPER - upload a single image file to Cloudinary
# Returns the secure URL string, or None if no file provided
# ============================================================
def upload_image(file, folder="wardrobe"):
    if not file or file.filename == '':
        return None
    configure_cloudinary()
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type="image"
    )
    return result.get('secure_url')

# ============================================================
# DASHBOARD - main wardrobe view with filtering
# ============================================================
@wardrobe.route('/')
@login_required
def dashboard():
    query = ClothingItem.query.filter_by(user_id=current_user.id)

    # ---- Apply filters from query params ----
    type_filter = request.args.get('type')
    color_filter = request.args.get('color')
    size_filter = request.args.get('size')
    material_filter = request.args.get('material')
    brand_filter = request.args.get('brand')
    season_filters = request.args.getlist('season')
    favorite_filter = request.args.get('favorite')

    if type_filter:
        query = query.filter(ClothingItem.type.ilike(f'%{type_filter}%'))
    if color_filter:
        query = query.filter(ClothingItem.color.ilike(f'%{color_filter}%'))
    if size_filter:
        query = query.filter_by(size=size_filter)
    if material_filter:
        query = query.filter(ClothingItem.material.ilike(f'%{material_filter}%'))
    if brand_filter:
        query = query.filter(ClothingItem.brand.ilike(f'%{brand_filter}%'))
    if season_filters:
        query = query.filter(or_(*[ClothingItem.season.ilike(f'%{s}%') for s in season_filters]))
    if favorite_filter:
        query = query.filter_by(favorite=True)

    items = query.all()

    # ---- Build dynamic filter options from user's items ----
    all_items = ClothingItem.query.filter_by(user_id=current_user.id).all()
    user_types = sorted(set(i.type for i in all_items if i.type))
    user_colors = sorted(set(i.color for i in all_items if i.color))
    user_materials = sorted(set(i.material for i in all_items if i.material))
    user_brands = sorted(set(i.brand for i in all_items if i.brand))
    user_seasons = sorted(set(
        s.strip() for i in all_items
        for s in i.season.split(',') if s.strip()
    ))

    return render_template('dashboard.html', items=items,
        type_filter=type_filter,
        color_filter=color_filter,
        size_filter=size_filter,
        material_filter=material_filter,
        brand_filter=brand_filter,
        season_filters=season_filters,
        favorite_filter=favorite_filter,
        user_types=user_types,
        user_colors=user_colors,
        user_materials=user_materials,
        user_brands=user_brands,
        user_seasons=user_seasons
    )

# ============================================================
# ADD ITEM - handles manual form + optional photo upload
# Photos uploaded to Cloudinary, URLs saved to database
# ============================================================
@wardrobe.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':

        # ---- Handle custom "Other" fields ----
        type_val = request.form.get('type')
        if type_val == 'Other':
            type_val = request.form.get('type_custom', '').strip().title()

        color_val = request.form.get('color')
        if color_val == 'Other':
            color_val = request.form.get('color_custom', '').strip().title()

        material_val = request.form.get('material')
        if material_val == 'Other':
            material_val = request.form.get('material_custom', '').strip().title()

        seasons = request.form.getlist('season')
        if 'Other' in seasons:
            seasons.remove('Other')
            custom_season = request.form.get('season_custom', '').strip().title()
            if custom_season:
                seasons.append(custom_season)
        season_val = ', '.join(seasons)

        # ---- Upload photos to Cloudinary (optional) ----
        front_image_url = upload_image(request.files.get('front_image'))
        tag_image_url = upload_image(request.files.get('tag_image'))

        # ---- Save item to database ----
        item = ClothingItem(
            type=type_val,
            color=color_val,
            size=request.form.get('size'),
            material=material_val,
            brand=request.form.get('brand'),
            season=season_val,
            favorite=True if request.form.get('favorite') else False,
            user_id=current_user.id,
            front_image_url=front_image_url,  # None if no photo uploaded
            tag_image_url=tag_image_url        # None if no photo uploaded
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added!')
        return redirect(url_for('wardrobe.dashboard'))

    return render_template('add_item.html')

# ============================================================
# EDIT ITEM - update existing clothing item details
# ============================================================
@wardrobe.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = ClothingItem.query.get_or_404(item_id)

    # ---- Security check: only owner can edit ----
    if item.user_id != current_user.id:
        flash('You do not have permission to edit this item.')
        return redirect(url_for('wardrobe.dashboard'))

    if request.method == 'POST':

        # ---- Handle custom "Other" fields ----
        type_val = request.form.get('type')
        if type_val == 'Other':
            type_val = request.form.get('type_custom', '').strip().title()

        color_val = request.form.get('color')
        if color_val == 'Other':
            color_val = request.form.get('color_custom', '').strip().title()

        material_val = request.form.get('material')
        if material_val == 'Other':
            material_val = request.form.get('material_custom', '').strip().title()

        seasons = request.form.getlist('season')
        if 'Other' in seasons:
            seasons.remove('Other')
            custom_season = request.form.get('season_custom', '').strip().title()
            if custom_season:
                seasons.append(custom_season)
        season_val = ', '.join(seasons)

        # ---- Update item fields ----
        item.type = type_val
        item.color = color_val
        item.size = request.form.get('size')
        item.material = material_val
        item.brand = request.form.get('brand')
        item.season = season_val
        item.favorite = True if request.form.get('favorite') else False

        # ---- Update photos if new ones were uploaded ----
        new_front = upload_image(request.files.get('front_image'))
        new_tag = upload_image(request.files.get('tag_image'))
        if new_front:
            item.front_image_url = new_front
        if new_tag:
            item.tag_image_url = new_tag

        db.session.commit()
        flash('Item updated!')
        return redirect(url_for('wardrobe.dashboard'))

    return render_template('edit_item.html', item=item)

# ============================================================
# DELETE ITEM - remove item from database
# ============================================================
@wardrobe.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = ClothingItem.query.get_or_404(item_id)

    # ---- Security check: only owner can delete ----
    if item.user_id != current_user.id:
        flash('You do not have permission to delete this item.')
        return redirect(url_for('wardrobe.dashboard'))

    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('wardrobe.dashboard'))

# ============================================================
# TOGGLE FAVORITE - mark/unmark item as favorite
# ============================================================
@wardrobe.route('/favorite/<int:item_id>', methods=['POST'])
@login_required
def toggle_favorite(item_id):
    item = ClothingItem.query.get_or_404(item_id)

    # ---- Security check: only owner can favorite ----
    if item.user_id != current_user.id:
        flash('Not authorized.')
        return redirect(url_for('wardrobe.dashboard'))

    item.favorite = not item.favorite
    db.session.commit()
    return redirect(url_for('wardrobe.dashboard'))

# ============================================================
# FAVORITES PAGE - shows only favorited items
# ============================================================
@wardrobe.route('/favorites')
@login_required
def favorites():
    items = ClothingItem.query.filter_by(user_id=current_user.id, favorite=True).all()
    return render_template('favorites.html', items=items)

# ============================================================
# SCAN TAG - Phase 2: send tag photo to Claude, extract label info
# Returns JSON: { brand, size, material, color }
# ============================================================
@wardrobe.route('/scan-tag', methods=['POST'])
@login_required
def scan_tag():
    api_key = current_app.config.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'error': 'AI scanning is not configured. Add ANTHROPIC_API_KEY to your .env file.'}), 500

    tag_file = request.files.get('tag_image')
    if not tag_file or tag_file.filename == '':
        return jsonify({'error': 'No image provided'}), 400

    image_data = base64.standard_b64encode(tag_file.read()).decode('utf-8')
    media_type = tag_file.content_type or 'image/jpeg'

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model='claude-opus-4-6',
        max_tokens=256,
        messages=[{
            'role': 'user',
            'content': [
                {
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': media_type,
                        'data': image_data
                    }
                },
                {
                    'type': 'text',
                    'text': (
                        'Read this clothing label and extract the following. '
                        'Return ONLY a JSON object with these exact keys:\n'
                        '- "brand": the brand name (e.g. "Nike", "Zara"), or "" if not visible\n'
                        '- "size": normalize to one of XS/S/M/L/XL/XXL if possible, '
                        'otherwise return the raw size string, or "" if not found\n'
                        '- "material": the main fabric/material (e.g. "Cotton", "Polyester"), or "" if not found\n'
                        '- "color": the color if stated on the tag, or "" if not found'
                    )
                }
            ]
        }],
        output_config={
            'format': {
                'type': 'json_schema',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'brand':    {'type': 'string'},
                        'size':     {'type': 'string'},
                        'material': {'type': 'string'},
                        'color':    {'type': 'string'}
                    },
                    'required': ['brand', 'size', 'material', 'color'],
                    'additionalProperties': False
                }
            }
        }
    )

    data = json.loads(response.content[0].text)
    return jsonify(data)

# ============================================================
# ANALYZE LABEL - Phase 2 comprehensive scan
# Claude Vision → DuckDuckGo search → FTC RN lookup
# Returns JSON: brand, size, material, category + info-only fields
# ============================================================
@wardrobe.route('/analyze-label', methods=['POST'])
@login_required
def analyze_label_route():
    api_key = current_app.config.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'error': 'AI scanning not configured. Add ANTHROPIC_API_KEY to your .env file.'}), 500

    tag_file = request.files.get('tag_image')
    if not tag_file or tag_file.filename == '':
        return jsonify({'error': 'No image provided'}), 400

    image_bytes = tag_file.read()
    media_type  = tag_file.content_type or 'image/jpeg'

    try:
        result = analyze_label(image_bytes, media_type, api_key)
    except anthropic.BadRequestError as e:
        msg = str(e)
        if 'credit balance is too low' in msg:
            return jsonify({'error': 'Anthropic account has no credits. Add credits at console.anthropic.com → Plans & Billing.'}), 402
        return jsonify({'error': f'API error: {msg}'}), 400
    except anthropic.AuthenticationError:
        return jsonify({'error': 'Invalid Anthropic API key. Check your .env file.'}), 401
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

    return jsonify(result)