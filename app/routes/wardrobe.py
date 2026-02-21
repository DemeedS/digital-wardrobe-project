from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
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
    season_filter = request.args.get('season')

    if type_filter:
        query = query.filter_by(type=type_filter)
    if color_filter:
        query = query.filter_by(color=color_filter)
    if size_filter:
        query = query.filter_by(size=size_filter)
    if material_filter:
        query = query.filter_by(material=material_filter)
    if season_filter:
        query = query.filter_by(season=season_filter)

    items = query.all()

    user_colors = db.session.query(ClothingItem.color).filter_by(user_id=current_user.id).distinct().all()
    user_colors = sorted([c[0] for c in user_colors])

    user_materials = db.session.query(ClothingItem.material).filter_by(user_id=current_user.id).distinct().all()
    user_materials = [m[0] for m in user_materials]

    return render_template('dashboard.html', items=items,
    type_filter=type_filter,
    color_filter=color_filter,
    size_filter=size_filter,
    material_filter=material_filter,
    season_filter=season_filter,
    user_colors=user_colors,
    user_materials=user_materials
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
        item = ClothingItem(
            type=request.form.get('type'),
            color=request.form.get('color', '').strip().title(),
            size=request.form.get('size'),
            material=request.form.get('material') if request.form.get('material') != 'Other' else request.form.get('material_custom', '').strip().title(),
            brand=request.form.get('brand'),
            season=request.form.get('season'),
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
        item.type = request.form.get('type')
        item.color = request.form.get('color', '').strip().title()
        item.size = request.form.get('size')
        item.material = request.form.get('material') if request.form.get('material') != 'Other' else request.form.get('material_custom', '').strip().title()        
        item.brand = request.form.get('brand')
        item.season = request.form.get('season')
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