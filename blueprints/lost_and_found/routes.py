from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import lost_and_found_bp
from config import ALLOWED_EXTENSIONS
from models import SessionLocal, LostFoundItem, ItemImage, upload_image_to_supabase, SUPABASE_LOSTFOUND_BUCKET, User, Category
from sqlalchemy.orm import selectinload
import re

@lost_and_found_bp.route('/')
@login_required
def dashboard():
    db = SessionLocal()
    items = db.query(LostFoundItem).options(selectinload(LostFoundItem.images)).filter_by(is_deleted=False).order_by(LostFoundItem.date.desc()).all()
    items_prior = db.query(LostFoundItem).options(selectinload(LostFoundItem.images)).filter_by(is_deleted=False).order_by(LostFoundItem.priority.desc()).all()
    total_items = len(items)
    total_lost = sum(1 for i in items if i.status == 'lost')
    total_found = sum(1 for i in items if i.status == 'found')
    recent_items = items_prior[:10]
    categories = db.query(Category).filter_by(type='lost_found').all()
    user = db.query(User).filter_by(id=current_user.id).first()
    # DEBUG: Print image URLs for each item
    for item in items:
        print(f"Item {item.id} images:", [img.image_url for img in item.images])
        if item.name.strip().lower() == "water bottle":
            print("Bottle item images:", [(img.id, img.item_id, img.item_type, img.image_url) for img in item.images])
    db.close()
    return render_template('lost_and_found/dashboard.html', user=user, items=items, total_items=total_items, total_lost=total_lost, total_found=total_found, recent_items=recent_items, categories=categories)

@lost_and_found_bp.route('/item/<int:item_id>')
@login_required
def item_detail(item_id):
    db = SessionLocal()
    item = db.query(LostFoundItem).options(selectinload(LostFoundItem.images)).filter_by(id=item_id, is_deleted=False).first()
    if not item:
        db.close()
        flash('Item not found', 'danger')
        return redirect(url_for('lost_and_found.dashboard'))
    user = db.query(User).filter_by(id=current_user.id).first()
    found_by_user = db.query(User).filter_by(id=item.found_by).first().username if item.found_by else None
    claimed_by_user = db.query(User).filter_by(id=item.claimed_by).first().username if item.claimed_by else None
    feedback = []  # TODO: Refactor feedback to use ORM if needed
    db.close()
    return render_template('lost_and_found/detail.html', item=item, feedback=feedback, user=user, found_by_user=found_by_user, claimed_by_user=claimed_by_user)

@lost_and_found_bp.route('/new', methods=['GET', 'POST'])
@login_required
def report():
    db = SessionLocal()
    user = db.query(User).filter_by(id=current_user.id).first()
    if user and user.username == 'temp':
        flash('You need to create an account to report items', 'warning')
        db.close()
        return redirect(url_for('auth.register'))
    if request.method == 'POST':
        form = request.form
        contact = form.get('contact_info', '').strip()
        if not re.fullmatch(r"\d{10}", contact):
            flash('Contact info must be a 10-digit phone number', 'danger')
            db.close()
            return redirect(url_for('lost_and_found.report'))
        file = request.files.get('image')
        img_url = None
        if file and file.filename and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            fn = secure_filename(file.filename)
            img_url = upload_image_to_supabase(file, fn, SUPABASE_LOSTFOUND_BUCKET)
        else:
            flash('Invalid file format. Only JPG, PNG, JPEG and WEBP are allowed.', 'danger')
            db.close()
            return redirect(url_for('lost_and_found.report'))
        # Convert latitude/longitude to float or None
        latitude = form.get('latitude')
        longitude = form.get('longitude')
        latitude = float(latitude) if latitude not in (None, "") else None
        longitude = float(longitude) if longitude not in (None, "") else None
        item = LostFoundItem(
            priority=form['priority'],
            name=form['name'],
            description=form['description'],
            category=form['category'],
            status=form['status'],
            date=form['date'],
            location=form['location'],
            contact_info=form['contact_info'],
            latitude=latitude,
            longitude=longitude,
            user_id=current_user.id
        )
        db.add(item)
        db.commit()
        if img_url:
            image = ItemImage(item_type='lost_found', item_id=item.id, image_url=img_url)
            db.add(image)
            db.commit()
        flash('Report submitted successfully!', 'success')
        db.close()
        return redirect(url_for('lost_and_found.dashboard'))
    categories = db.query(Category).filter_by(type='lost_found').all()
    db.close()
    return render_template('lost_and_found/report.html', categories=categories)

@lost_and_found_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    db = SessionLocal()
    item = db.query(LostFoundItem).filter_by(id=item_id).first()
    if not item:
        flash('Item not found', 'danger')
        db.close()
        return redirect(url_for('lost_and_found.dashboard'))
    user = db.query(User).filter_by(id=current_user.id).first()
    if not (item.user_id == current_user.id or user.is_admin):
        flash('You are not authorized to edit this item', 'danger')
        db.close()
        return redirect(url_for('lost_and_found.dashboard'))
    if request.method == 'POST':
        form = request.form
        contact = form.get('contact_info', '').strip()
        if not re.fullmatch(r"\d{10}", contact):
            flash('Contact info must be a 10-digit phone number', 'danger')
            db.close()
            return redirect(url_for('lost_and_found.edit_item', item_id=item_id))
        file = request.files.get('image_path')
        img_url = None
        if file and file.filename and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            fn = secure_filename(file.filename)
            img_url = upload_image_to_supabase(file, fn, SUPABASE_LOSTFOUND_BUCKET)
            image = ItemImage(item_type='lost_found', item_id=item.id, image_url=img_url)
            db.add(image)
        # Update item fields
        item.priority = form['priority']
        item.name = form['name']
        item.description = form['description']
        item.category = form['category']
        item.status = form['status']
        item.location = form['location']
        item.contact_info = form['contact_info']
        # Clear tags if status changed
        if form['status'] != 'found':
            item.found_by = None
        if form['status'] != 'claimed':
            item.claimed_by = None
        db.commit()
        flash('Item updated successfully!', 'success')
        db.close()
        return redirect(url_for('lost_and_found.item_detail', item_id=item_id))
    categories = db.query(Category).filter_by(type='lost_found').all()
    db.close()
    return render_template('lost_and_found/edit.html', item=item, categories=categories)

@lost_and_found_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    db = SessionLocal()
    item = db.query(LostFoundItem).filter_by(id=item_id).first()
    if not item:
        flash('Item not found', 'danger')
        db.close()
        return redirect(url_for('lost_and_found.dashboard'))
    user = db.query(User).filter_by(id=current_user.id).first()
    if not (item.user_id == current_user.id or user.is_admin):
        flash('You are not authorized to delete this item', 'danger')
        db.close()
        return redirect(url_for('lost_and_found.dashboard'))
    # Soft delete the item
    item.is_deleted = True
    db.commit()
    flash('Item deleted successfully!', 'success')
    db.close()
    return redirect(url_for('lost_and_found.dashboard'))

@lost_and_found_bp.route('/item/<int:item_id>/claim', methods=['POST'])
@login_required
def claim_item(item_id):
    db = SessionLocal()
    item = db.query(LostFoundItem).filter_by(id=item_id, is_deleted=False).first()
    if not item or item.status != 'found':
        flash('Invalid operation.', 'danger')
        db.close()
        return redirect(url_for('lost_and_found.item_detail', item_id=item_id))
    if item.user_id == current_user.id:
        flash('Cannot claim your own item.', 'warning')
        db.close()
        return redirect(url_for('lost_and_found.item_detail', item_id=item_id))
    # Update status and claimer
    item.status = 'claimed'
    item.claimed_by = current_user.id
    db.commit()
    flash('Item claimed successfully!', 'success')
    db.close()
    return redirect(url_for('lost_and_found.item_detail', item_id=item_id))

@lost_and_found_bp.route('/item/<int:item_id>/found_user', methods=['POST'])
@login_required
def found_user(item_id):
    db = SessionLocal()
    item = db.query(LostFoundItem).filter_by(id=item_id, is_deleted=False).first()
    if not item or item.status != 'lost':
        flash('Invalid operation.', 'danger')
        db.close()
        return redirect(url_for('lost_and_found.item_detail', item_id=item_id))
    if item.user_id == current_user.id:
        flash('Cannot mark your own item as found.', 'warning')
        db.close()
        return redirect(url_for('lost_and_found.item_detail', item_id=item_id))
    # Update status and finder
    item.status = 'found'
    item.found_by = current_user.id
    db.commit()
    flash('Item marked as found!', 'success')
    db.close()
    return redirect(url_for('lost_and_found.item_detail', item_id=item_id))

@lost_and_found_bp.route('/item/<int:item_id>/remove_claim', methods=['POST'])
@login_required
def remove_claim(item_id):
    db = SessionLocal()
    item = db.query(LostFoundItem).filter_by(id=item_id, is_deleted=False).first()
    user = db.query(User).filter_by(id=current_user.id).first()
    # Only owner or admin can remove claim
    if not item or not (item.user_id == current_user.id or user.is_admin):
        flash('Not authorized to remove claim.', 'danger')
        db.close()
        return redirect(url_for('lost_and_found.dashboard'))
    # Only remove for claimed items
    if item.status != 'claimed':
        flash('Item is not claimed.', 'warning')
        db.close()
        return redirect(url_for('lost_and_found.dashboard'))
    # Reset status and clear claimer
    item.status = 'found'
    item.claimed_by = None
    db.commit()
    flash('Claim removed; item status set back to Found.', 'success')
    db.close()
    return redirect(url_for('lost_and_found.dashboard'))

@lost_and_found_bp.route('/item/<int:item_id>/remove_found', methods=['POST'])
@login_required
def remove_found(item_id):
    db = SessionLocal()
    item = db.query(LostFoundItem).filter_by(id=item_id, is_deleted=False).first()
    user = db.query(User).filter_by(id=current_user.id).first()
    # Only owner or admin can remove found tag
    if not item or not (item.user_id == current_user.id or user.is_admin):
        flash('Not authorized to remove found tag.', 'danger')
        db.close()
        return redirect(url_for('lost_and_found.dashboard'))
    # Only if a found_by tag exists
    if not item.found_by:
        flash('No found tag to remove.', 'warning')
        db.close()
        return redirect(url_for('lost_and_found.item_detail', item_id=item_id))
    # Clear found_by tag but keep status and category unchanged
    item.found_by = None
    db.commit()
    flash('Found tag removed.', 'success')
    db.close()
    return redirect(request.referrer or url_for('lost_and_found.dashboard'))