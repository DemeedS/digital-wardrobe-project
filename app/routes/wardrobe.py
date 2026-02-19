from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import ClothingItem

wardrobe = Blueprint('wardrobe', __name__)

@wardrobe.route('/')
@login_required
def dashboard():
    items = ClothingItem.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', items=items)

@wardrobe.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        item = ClothingItem(
            type=request.form.get('type'),
            color=request.form.get('color'),
            size=request.form.get('size'),
            material=request.form.get('material'),
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
        item.color = request.form.get('color')
        item.size = request.form.get('size')
        item.material = request.form.get('material')
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