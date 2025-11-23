from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, logout_user, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
from ..extensions import db, login_manager

from ..models import User, APIKey

site_path = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(site_path, 'static')
site = Blueprint('site', __name__, template_folder='templates', static_folder=static_folder, static_url_path='/site/static')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@site.route('/')
@login_required
def home():
    if not current_user.keys:
        flash('Please add an API key on the settings page to view stats.', 'warning')
        return render_template('home.html', stats=None)

    # Use the first API key for stats
    api_key_to_use = current_user.keys[0].key

    try:
        headers = {'Authorization': f'Bearer {api_key_to_use}'}
        response = requests.get('https://ai.hackclub.com/proxy/v1/stats', headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        stats = response.json()
    except requests.exceptions.RequestException as e:
        flash(f'Error fetching stats: {e}', 'danger')
        stats = None
    return render_template('home.html', stats=stats)

@site.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        if api_key:
            # Check if key already exists for this user
            existing_key = APIKey.query.filter_by(key=api_key, user_id=current_user.id).first()
            if not existing_key:
                new_key = APIKey(key=api_key, user_id=current_user.id)
                db.session.add(new_key)
                db.session.commit()
                flash('API Key added successfully!', 'success')
            else:
                flash('This API Key has already been added.', 'info')
        else:
            flash('API Key cannot be empty.', 'warning')
        return redirect(url_for('site.settings'))

    keys = current_user.keys
    return render_template('settings.html', keys=keys)

@site.route('/delete_key/<int:key_id>', methods=['POST'])
@login_required
def delete_key(key_id):
    key_to_delete = APIKey.query.get_or_404(key_id)
    if key_to_delete.user_id != current_user.id:
        # Unauthorized
        return redirect(url_for('site.settings'))

    db.session.delete(key_to_delete)
    db.session.commit()
    flash('API Key deleted successfully!', 'success')
    return redirect(url_for('site.settings'))

@site.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('site.home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            return redirect(url_for('site.home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@site.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('site.home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('site.signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('site.login'))
    return render_template('signup.html')

@site.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('site.login'))
