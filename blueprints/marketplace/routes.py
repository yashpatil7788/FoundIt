from flask import render_template, redirect, url_for, request, flash, make_response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import marketplace_bp
from config import ALLOWED_EXTENSIONS, SUPABASE_MARKETPLACE_BUCKET
from models import SessionLocal, MarketplaceItem, ItemImage, upload_image_to_supabase, User, Category

@marketplace_bp.route('/')
@login_required
def dashboard():
    db = SessionLocal()
    items = db.query(MarketplaceItem).filter_by(is_deleted=False).order_by(MarketplaceItem.date.desc()).all()
    total_items = len(items)
    total_available = sum(1 for i in items if i.status == 'available')
    total_sold = sum(1 for i in items if i.status == 'sold')
    recent_items = items[:10]
    categories = db.query(Category).filter_by(type='marketplace').all()
    user = db.query(User).filter_by(id=current_user.id).first()
    db.close()
    return render_template('marketplace/dashboard.html', user=user, items=items, total_items=total_items, total_available=total_available, total_sold=total_sold, recent_items=recent_items, categories=categories)

@marketplace_bp.route('/item/<int:item_id>')
@login_required
def item_detail(item_id):
    db = SessionLocal()
    item = db.query(MarketplaceItem).filter_by(id=item_id, is_deleted=False).first()
    if not item:
        db.close()
        flash('Item not found', 'danger')
        return redirect(url_for('marketplace.dashboard'))
    user = db.query(User).filter_by(id=current_user.id).first()
    feedback = []  # TODO: Refactor feedback to use ORM if needed
    db.close()
    return render_template('marketplace/detail.html', item=item, feedback=feedback, user=user)

@marketplace_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    db = SessionLocal()
    # Check if user is temporary
    user = db.query(User).filter_by(id=current_user.id).first()
    if user and user.username == 'temp':
        flash('You need to create an account to list items for sale', 'warning')
        db.close()
        return redirect(url_for('auth.register'))
    if request.method == 'POST':
        form = request.form
        file = request.files.get('image')
        img_url = None
        if file and file.filename and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            fn = secure_filename(file.filename)
            img_url = upload_image_to_supabase(file, fn, SUPABASE_MARKETPLACE_BUCKET)
        else:
            flash('Invalid file format. Only JPG, PNG, JPEG and WEBP are allowed.', 'danger')
            db.close()
            return redirect(url_for('marketplace.create'))
        # Create item
        item = MarketplaceItem(
            name=form['name'],
            description=form.get('description'),
            price=form['price'],
            category=form['category'],
            condition=form['condition'],
            location=form['location'],
            contact_info=form['contact_info'],
            user_id=current_user.id,
            status='available'
        )
        db.add(item)
        db.commit()
        # Add image
        if img_url:
            image = ItemImage(item_type='marketplace', item_id=item.id, image_url=img_url)
            db.add(image)
            db.commit()
        flash('Item listed successfully!', 'success')
        db.close()
        return redirect(url_for('marketplace.dashboard'))
    categories = db.query(Category).filter_by(type='marketplace').all()
    db.close()
    return render_template('marketplace/create.html', categories=categories)

@marketplace_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    db = SessionLocal()
    item = db.query(MarketplaceItem).filter_by(id=item_id).first()
    if not item:
        flash('Item not found', 'danger')
        db.close()
        return redirect(url_for('marketplace.dashboard'))
    user = db.query(User).filter_by(id=current_user.id).first()
    if not (item.user_id == current_user.id or user.is_admin):
        flash('You are not authorized to edit this item', 'danger')
        db.close()
        return redirect(url_for('marketplace.dashboard'))
    if request.method == 'POST':
        form = request.form
        file = request.files.get('image_path')
        img_url = None
        if file and file.filename and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            fn = secure_filename(file.filename)
            img_url = upload_image_to_supabase(file, fn, SUPABASE_MARKETPLACE_BUCKET)
            # Add new image record
            image = ItemImage(item_type='marketplace', item_id=item.id, image_url=img_url)
            db.add(image)
        # Update item fields
        item.name = form['name']
        item.description = form.get('description')
        item.price = form['price']
        item.category = form['category']
        item.condition = form['condition']
        item.location = form['location']
        item.contact_info = form['contact_info']
        item.status = form['status']
        db.commit()
        flash('Item updated successfully!', 'success')
        db.close()
        return redirect(url_for('marketplace.item_detail', item_id=item_id))
    categories = db.query(Category).filter_by(type='marketplace').all()
    db.close()
    return render_template('marketplace/edit.html', item=item, categories=categories)

@marketplace_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    db = SessionLocal()
    item = db.query(MarketplaceItem).filter_by(id=item_id).first()
    if not item:
        flash('Item not found', 'danger')
        db.close()
        return redirect(url_for('marketplace.dashboard'))
    user = db.query(User).filter_by(id=current_user.id).first()
    if not (item.user_id == current_user.id or user.is_admin):
        flash('You are not authorized to delete this item', 'danger')
        db.close()
        return redirect(url_for('marketplace.dashboard'))
    # Soft delete the item
    item.is_deleted = True
    db.commit()
    flash('Item deleted successfully!', 'success')
    db.close()
    return redirect(url_for('marketplace.dashboard'))

@marketplace_bp.route('/buy/<int:item_id>')
@login_required
def buy_item(item_id):
    db = SessionLocal()
    item = db.query(MarketplaceItem).filter_by(id=item_id, is_deleted=False).first()
    if not item:
        flash('Item not found', 'danger')
        return redirect(url_for('marketplace.dashboard'))
    if item.user_id == current_user.id:
        flash('You cannot buy your own item', 'warning')
        return redirect(url_for('marketplace.item_detail', item_id=item_id))
    seller = db.query(User).filter_by(id=item.user_id).first()
    content = []
    content.append(f"Seller Details for Item: {item.name}")
    content.append(f"Username: {seller.username if seller else 'N/A'}")
    content.append(f"Email: {seller.email if seller else 'N/A'}")
    content.append(f"Contact: {item.contact_info}")
    text = '\n'.join(content)
    item.status = 'sold'
    db.commit()
    response = make_response(text)
    response.headers.set('Content-Disposition', f'attachment; filename=seller_{item_id}.txt')
    response.mimetype = 'text/plain'
    db.close()
    return response