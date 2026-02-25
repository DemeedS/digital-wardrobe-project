from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models import ClothingItem

wardrobe = Blueprint('wardrobe', __name__)

@wardrobe.route('/')
@login_required
def dashboard():
    query = ClothingItem.query.filter_by(user_id=current_user.id)

    type_filter = request.args.get('type')
    color_filter = request.args.get('color')
    size_filter = request.args.get('size')
    material_filter = request.args.get('material')
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
    if season_filters:
        query = query.filter(or_(*[ClothingItem.season.ilike(f'%{s}%') for s in season_filters]))
    if favorite_filter:
        query = query.filter_by(favorite=True)

    items = query.all()

    user_types = sorted(set(i.type for i in ClothingItem.query.filter_by(user_id=current_user.id).all() if i.type))
    user_colors = sorted(set(i.color for i in ClothingItem.query.filter_by(user_id=current_user.id).all() if i.color))
    user_materials = sorted(set(i.material for i in ClothingItem.query.filter_by(user_id=current_user.id).all() if i.material))
    user_seasons = sorted(set(
        s.strip() for i in ClothingItem.query.filter_by(user_id=current_user.id).all()
        for s in i.season.split(',') if s.strip()
    ))

    return render_template('dashboard.html', items=items,
        type_filter=type_filter,
        color_filter=color_filter,
        size_filter=size_filter,
        material_filter=material_filter,
        season_filters=season_filters,
        favorite_filter=favorite_filter,
        user_types=user_types,
        user_colors=user_colors,
        user_materials=user_materials,
        user_seasons=user_seasons
    )

@wardrobe.route('/favorite/<int:item_id>', methods=['POST'])
@login_required
def toggle_favorite(item_id):
    item = ClothingItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Not authorized.')
        return redirect(url_for('wardrobe.dashboard'))
    item.favorite = not item.favorite
    db.session.commit()
    return redirect(url_for('wardrobe.dashboard'))

@wardrobe.route('/favorites')
@login_required
def favorites():
    items = ClothingItem.query.filter_by(user_id=current_user.id, favorite=True).all()
    return render_template('favorites.html', items=items)

@wardrobe.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
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

        item = ClothingItem(
            type=type_val,
            color=color_val,
            size=request.form.get('size'),
            material=material_val,
            brand=request.form.get('brand'),
            season=season_val,
            favorite=True if request.form.get('favorite') else False,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added!')
        return redirect(url_for('wardrobe.dashboard'))
    return render_template('add_item.html')

@wardrobe.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = ClothingItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to edit this item.')
        return redirect(url_for('wardrobe.dashboard'))
    if request.method == 'POST':
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

        item.type = type_val
        item.color = color_val
        item.size = request.form.get('size')
        item.material = material_val
        item.brand = request.form.get('brand')
        item.season = season_val
        item.favorite = True if request.form.get('favorite') else False
        db.session.commit()
        flash('Item updated!')
        return redirect(url_for('wardrobe.dashboard'))
    return render_template('edit_item.html', item=item)

@wardrobe.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = ClothingItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to delete this item.')
        return redirect(url_for('wardrobe.dashboard'))
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('wardrobe.dashboard'))