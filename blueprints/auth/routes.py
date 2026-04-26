from flask import render_template, redirect, url_for, request, flash, make_response
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message
from extensions import mail
from config import SECRET_KEY, MAIL_USERNAME
from werkzeug.security import check_password_hash, generate_password_hash

from . import auth_bp
import models  # Changed from relative to absolute import

serializer = URLSafeTimedSerializer(SECRET_KEY)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('lost_and_found.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = models.SessionLocal()
        user = db.query(models.User).filter_by(username=username).first()
        db.close()
        if user and check_password_hash(user.password, password):
            if not user.is_confirmed:
                flash('Please confirm your email before logging in.', 'warning')
                return redirect(url_for('auth.login'))
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('lost_and_found.dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/continue_without_login')
def continue_without_login():
    user = models.get_user_by_username('temp')
    if user:
        login_user(models.User(user['id']))
        return redirect(url_for('lost_and_found.dashboard'))
    
    flash('Temporary user does not exist!', 'warning')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('lost_and_found.dashboard'))
    
    cookie = request.cookies.get('rate_limit')
    if request.method == 'POST' and cookie:
        last = datetime.strptime(cookie, '%Y-%m-%d %H:%M:%S')
        if datetime.now() - last < timedelta(seconds=60):
            flash('Rate-limited. Wait a minute.', 'warning')
            return redirect(url_for('auth.register'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash("Passwords don't match.", 'danger')
            return redirect(url_for('auth.register'))
        
        db = models.SessionLocal()
        # Check for duplicate username or email
        existing_user = db.query(models.User).filter(
            (models.User.username == username) | (models.User.email == email)
        ).first()
        if existing_user:
            db.close()
            flash('Username or email already exists. Please choose another.', 'danger')
            return redirect(url_for('auth.register'))
        # Use hashed password for security
        hashed_password = generate_password_hash(password)
        user = models.User(username=username, email=email, password=hashed_password)
        db.add(user)
        db.commit()
        user_id = user.id
        db.close()
        # Send confirmation email
        token = serializer.dumps(email, salt='email-confirm')
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        print(f'Confirmation URL: {confirm_url}')
        msg = Message('Confirm Your Email', sender=MAIL_USERNAME, recipients=[email])
        msg.body = f'Please click the link to confirm your email: {confirm_url}'
        try:
            mail.send(msg)
            flash('Registration successful! Please check your email to confirm your account.', 'success')
            resp = make_response(redirect(url_for('auth.login')))
            resp.set_cookie('rate_limit', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), max_age=60)
            return resp
        except Exception as e:
            flash('Failed to send confirmation email. Please contact support.', 'danger')
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash('The confirmation link has expired.', 'danger')
        return redirect(url_for('auth.login'))
    except BadSignature:
        flash('Invalid confirmation link.', 'danger')
        return redirect(url_for('auth.login'))
    db = models.SessionLocal()
    user = db.query(models.User).filter_by(email=email).first()
    if user:
        user.is_confirmed = True
        db.commit()
        flash('Email confirmed! You can now log in.', 'success')
    else:
        flash('User not found.', 'danger')
    db.close()
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = models.SessionLocal()
    user = db.query(models.User).filter_by(id=current_user.id).first()
    if not user:
        db.close()
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    # Add created_at and role for the template if missing
    if not user.created_at:
        user.created_at = datetime.now()
    if not user.role:
        user.role = 'student'

    # Only show items that are not deleted
    lost_found_items = db.query(models.LostFoundItem).filter_by(user_id=current_user.id, is_deleted=False).all()
    marketplace_items = db.query(models.MarketplaceItem).filter_by(user_id=current_user.id, is_deleted=False).all()

    # Get recent items for the dashboard tab (not deleted)
    recent_items = []
    for item in lost_found_items[:5]:
        item.type = 'lost_found'
        recent_items.append(item)
    for item in marketplace_items[:5]:
        item.type = 'marketplace'
        recent_items.append(item)
    recent_items.sort(key=lambda x: x.date if hasattr(x, 'date') else datetime.min, reverse=True)
    recent_items = recent_items[:10]

    if request.method == 'POST':
        # Handle deletion of lost and found items
        if request.form.get('lost_found_id'):
            item_id = request.form.get('lost_found_id')
            item = db.query(models.LostFoundItem).filter_by(id=item_id, user_id=current_user.id, is_deleted=False).first()
            if item and (item.user_id == current_user.id or user.is_admin):
                item.is_deleted = True
                db.commit()
                flash('Item deleted successfully.', 'success')
            else:
                flash('You are not authorized to delete this item.', 'danger')
            db.close()
            return redirect(url_for('auth.profile'))
        # Handle deletion of marketplace items
        if request.form.get('market_id'):
            item_id = request.form.get('market_id')
            item = db.query(models.MarketplaceItem).filter_by(id=item_id, user_id=current_user.id, is_deleted=False).first()
            if item and (item.user_id == current_user.id or user.is_admin):
                item.is_deleted = True
                db.commit()
                flash('Item deleted successfully.', 'success')
            else:
                flash('You are not authorized to delete this item.', 'danger')
            db.close()
            return redirect(url_for('auth.profile'))
    db.close()
    return render_template('auth/profile.html', user=user, 
                          lost_found_items=lost_found_items, 
                          marketplace_items=marketplace_items,
                          recent_items=recent_items)

@auth_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    db = models.SessionLocal()
    user = db.query(models.User).filter_by(id=current_user.id).first()
    if not user:
        db.close()
        flash('User not found', 'danger')
        return redirect(url_for('auth.profile'))
    # Get form data
    username = request.form.get('username')
    email = request.form.get('email')
    role = request.form.get('role')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    # Update username if changed and not already taken
    if username and username != user.username:
        existing_user = db.query(models.User).filter_by(username=username).first()
        if existing_user:
            db.close()
            flash('Username already taken.', 'danger')
            return redirect(url_for('auth.profile'))
        user.username = username
    # Update email if changed and not already taken
    if email and email != user.email:
        existing_email = db.query(models.User).filter_by(email=email).first()
        if existing_email:
            db.close()
            flash('Email already taken.', 'danger')
            return redirect(url_for('auth.profile'))
        user.email = email
    # Update role if provided
    if role:
        user.role = role
    # Update password if provided and matches
    if new_password:
        if new_password != confirm_password:
            db.close()
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.profile'))
        from werkzeug.security import generate_password_hash, check_password_hash
        if not check_password_hash(user.password, current_password):
            db.close()
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.profile'))
        user.password = generate_password_hash(new_password)
    db.commit()
    db.close()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('auth.profile'))