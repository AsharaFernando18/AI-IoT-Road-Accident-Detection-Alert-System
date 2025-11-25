"""
Flask Application with Plotly Dash Integration
Main dashboard for RoadSafeNet
"""

from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify, Response, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import lru_cache, wraps
import bcrypt
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import pandas as pd
import threading
import time

sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from prisma import Prisma

# Initialize Flask app
server = Flask(__name__, 
              template_folder=str(Config.TEMPLATES_DIR),
              static_folder=str(Config.STATIC_DIR))
server.config['SECRET_KEY'] = Config.SECRET_KEY
server.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # Session expires after 1 hour
server.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
server.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
server.config['SESSION_COOKIE_HTTPONLY'] = True
server.config['REMEMBER_COOKIE_DURATION'] = timedelta(hours=1)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'  # Strong session protection

# Database
db = Prisma()

# Role-based access control decorators
def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def operator_required(f):
    """Decorator to require operator or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if current_user.role not in ['admin', 'operator']:
            flash('Access denied. Operator or Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Simple in-memory cache for performance
_cache = {}
_cache_timeout = 5  # Cache for 5 seconds

def get_cached(key, fetch_func):
    """Simple cache helper - returns cached data if fresh, otherwise fetches new"""
    now = time.time()
    if key in _cache:
        data, timestamp = _cache[key]
        if now - timestamp < _cache_timeout:
            return data
    
    # Fetch new data
    data = fetch_func()
    _cache[key] = (data, now)
    return data

# Background asyncio loop runner
_bg_loop = None
_bg_thread = None
_bg_lock = threading.Lock()

def _start_bg_loop():
    """Start a background event loop in a separate daemon thread."""
    global _bg_loop, _bg_thread
    with _bg_lock:
        if _bg_loop is not None and _bg_loop.is_running():
            return

        _bg_loop = asyncio.new_event_loop()

        def run_loop(loop: asyncio.AbstractEventLoop):
            asyncio.set_event_loop(loop)
            loop.run_forever()

        _bg_thread = threading.Thread(target=run_loop, args=(_bg_loop,), daemon=True)
        _bg_thread.start()


def run_in_background(coro, timeout=10):
    """Run coroutine in the background event loop and return its result.

    This submits the coroutine to the dedicated background loop using
    asyncio.run_coroutine_threadsafe which avoids creating and closing
    event loops per-request and prevents loop-binding issues with async
    libraries like httpx/prisma.
    """
    global _bg_loop
    if _bg_loop is None or not _bg_loop.is_running():
        _start_bg_loop()

    future = asyncio.run_coroutine_threadsafe(coro, _bg_loop)
    return future.result(timeout)

# Ensure the background loop starts at import time so Flask requests can use it
_start_bg_loop()


class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, user_data):
        # Handle both dict-like objects (sqlite3.Row) and object attributes
        if isinstance(user_data, dict) or hasattr(user_data, 'keys'):
            self.id = user_data['id']
            self.username = user_data['username']
            self.email = user_data['email']
            self.role = user_data['role']
            self._is_active = user_data['is_active']
        else:
            self.id = user_data.id
            self.username = user_data.username
            self.email = user_data.email
            self.role = user_data.role
            self._is_active = user_data.is_active
    
    @property
    def is_active(self):
        """Return whether user is active"""
        return self._is_active


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID"""
    try:
        # Use direct SQLite connection
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM User WHERE id = ?', (int(user_id),))
        user_data = cursor.fetchone()
        conn.close()
        
        return User(user_data) if user_data else None
    except Exception as e:
        print(f"Error loading user: {e}")
        import traceback
        traceback.print_exc()
        return None


# Flask Routes
@server.route('/')
def index():
    """Redirect to login page (logout if already authenticated)"""
    # Always show login page at root - logout existing sessions
    if current_user.is_authenticated:
        logout_user()
        session.clear()
    return redirect(url_for('login'))


@server.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    # Allow viewing login page with ?force=1 parameter even if authenticated
    force_login = request.args.get('force') == '1'
    
    if current_user.is_authenticated and not force_login:
        return redirect('/dashboard')
    
    # If force login, logout first
    if force_login and current_user.is_authenticated:
        logout_user()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            # Use direct SQLite connection
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM User WHERE username = ?', (username,))
            user_data = cursor.fetchone()
            conn.close()
        except Exception as e:
            print(f"Login error: {e}")
            import traceback
            traceback.print_exc()
            user_data = None
        
        if user_data:
            # Check password using bcrypt
            password_bytes = password.encode('utf-8')
            hash_bytes = user_data['password_hash'].encode('utf-8')
            password_match = bcrypt.checkpw(password_bytes, hash_bytes)
            
            if password_match:
                if user_data['is_active']:
                    user = User(user_data)
                    # Don't use remember_me - session will expire when browser closes or after timeout
                    login_user(user, remember=False)
                    session.permanent = False  # Session ends when browser closes
                    
                    # Store user location data in session for filtering
                    session['user_city'] = user_data['city'] if user_data['city'] else None
                    session['user_latitude'] = user_data['latitude'] if user_data['latitude'] else None
                    session['user_longitude'] = user_data['longitude'] if user_data['longitude'] else None
                    session['user_role'] = user_data['role'] if user_data['role'] else 'viewer'
                    
                    # Return JSON for AJAX, redirect for regular POST
                    if is_ajax:
                        return jsonify({'success': True, 'redirect': '/dashboard'})
                    return redirect('/dashboard')
                else:
                    error_msg = 'Your account is currently inactive. Please contact the administrator.'
                    if is_ajax:
                        return jsonify({'success': False, 'message': error_msg})
                    flash(error_msg, 'danger')
            else:
                error_msg = 'Invalid username or password. Please try again.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg})
                flash(error_msg, 'danger')
        else:
            error_msg = 'Invalid username or password. Please try again.'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg})
            flash(error_msg, 'danger')
    
    return render_template('login.html')


@server.route('/logout')
@login_required
def logout():
    """Logout and stop accident detection"""
    logout_user()
    session.clear()  # Clear all session data
    
    # Stop accident detection when user logs out
    try:
        from utils.video_stream import video_stream
        video_stream.stop()
        print("🛑 Accident detection stopped - User logged out")
    except Exception as e:
        print(f"⚠️ Error stopping video stream on logout: {e}")
    
    flash('You have been logged out successfully. See you next time!', 'success')
    return redirect(url_for('login'))


@server.route('/dashboard')
@server.route('/dashboard/')
@login_required
def dashboard():
    """Main dashboard page"""
    user_city = session.get('user_city', 'All Locations')
    user_lat = session.get('user_latitude', None)
    user_lon = session.get('user_longitude', None)
    
    return render_template('dashboard.html', 
                          user_role=current_user.role, 
                          username=current_user.username,
                          user_city=user_city,
                          user_latitude=user_lat,
                          user_longitude=user_lon)


@server.route('/video_feed')
@login_required
def video_feed():
    """Video streaming route with YOLOv10 detection"""
    from utils.video_stream import video_feed as stream_video
    return stream_video()


@server.route('/cctv_video/<filename>')
@login_required
def cctv_video(filename):
    """Serve CCTV video file from cctv_videos folder"""
    cctv_videos_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cctv_videos')
    return send_from_directory(cctv_videos_path, filename)


@server.route('/api/latest_accident')
@login_required
def get_latest_accident():
    """API endpoint to get latest accident for popup"""
    from utils.video_stream import video_stream
    
    if video_stream.latest_accident:
        print(f"✅ Returning latest accident: {video_stream.latest_accident}")
        return jsonify({
            'success': True,
            'accident': video_stream.latest_accident
        })
    else:
        return jsonify({
            'success': False,
            'accident': None
        })


@server.route('/api/clear_accident_alert', methods=['POST'])
@login_required
def clear_accident_alert():
    """Clear the latest accident alert"""
    from utils.video_stream import video_stream
    video_stream.latest_accident = None
    return jsonify({'success': True})


@server.route('/api/start_monitoring', methods=['POST'])
@login_required
@operator_required
def start_monitoring():
    """Start video monitoring and detection (Operator/Admin only)"""
    from utils.video_stream import video_stream
    
    if not video_stream.is_running:
        video_stream.start()
        print("🎥 Video stream with YOLOv10 detection started by user")
        return jsonify({
            'success': True,
            'message': 'Monitoring started successfully'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Monitoring already running'
        })


@server.route('/api/stop_monitoring', methods=['POST'])
@login_required
@operator_required
def stop_monitoring():
    """Stop video monitoring and detection (Operator/Admin only)"""
    from utils.video_stream import video_stream
    
    if video_stream.is_running:
        video_stream.stop()
        print("🛑 Video stream stopped by user")
        return jsonify({
            'success': True,
            'message': 'Monitoring stopped successfully'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Monitoring not running'
        })


@server.route('/api/monitoring_status', methods=['GET'])
@login_required
def monitoring_status():
    """Get current monitoring status"""
    from utils.video_stream import video_stream
    
    return jsonify({
        'success': True,
        'is_running': video_stream.is_running,
        'detection_enabled': video_stream.detection_enabled
    })


@server.route('/api/toggle_detection', methods=['POST'])
@login_required
@operator_required
def toggle_detection():
    """Toggle YOLOv10 detection on/off (Operator/Admin only)"""
    from utils.video_stream import video_stream
    
    data = request.get_json()
    enable = data.get('enable', True)
    
    video_stream.detection_enabled = enable
    
    return jsonify({
        'success': True,
        'detection_enabled': video_stream.detection_enabled,
        'message': 'Detection enabled' if enable else 'Detection disabled - showing raw video'
    })


@server.route('/api/emergency_notifications')
@login_required
def get_emergency_notifications():
    """API endpoint to get emergency notifications sent"""
    from utils.video_stream import video_stream
    
    return jsonify({
        'success': True,
        'notifications': video_stream.accident_notifications
    })


@server.route('/dashboard/analytics')
@server.route('/dashboard/analytics/')
@login_required
def analytics():
    """Analytics page"""
    return render_template('analytics.html', user_role=current_user.role, username=current_user.username)


@server.route('/dashboard/notifications')
@server.route('/dashboard/notifications/')
@login_required
def notifications_page():
    """Notifications management page"""
    return render_template('notifications.html', user_role=current_user.role, username=current_user.username)


@server.route('/dashboard/users')
@server.route('/dashboard/users/')
@login_required
@admin_required
def users_page():
    """User management page (Admin only)"""
    return render_template('users.html', user_role=current_user.role, username=current_user.username)


@server.route('/api/incidents')
@login_required
def get_incidents():
    """API endpoint to get active incidents"""
    def fetch_incidents():
        try:
            # Direct SQLite query for speed
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get user's city from session for location-based filtering
            user_city = session.get('user_city', None)
            user_role = session.get('user_role', 'viewer')
            
            # Admins see all incidents, others see only their city's incidents
            if user_role == 'admin' or not user_city:
                # Get recent unresolved accidents (all locations) - case insensitive
                cursor.execute('''
                    SELECT id, timestamp, location_name, city, country, severity, status, 
                           location_lat, location_lon, confidence
                    FROM Accident
                    WHERE UPPER(status) NOT IN ('RESOLVED', 'FALSE_ALARM')
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''')
            else:
                # Filter by user's city - case insensitive
                cursor.execute('''
                    SELECT id, timestamp, location_name, city, country, severity, status, 
                           location_lat, location_lon, confidence
                    FROM Accident
                    WHERE UPPER(status) NOT IN ('RESOLVED', 'FALSE_ALARM') 
                    AND (city = ? OR city IS NULL)
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''', (user_city,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Format data for frontend
            incidents = []
            for row in rows:
                lat = row['location_lat'] or 0
                lon = row['location_lon'] or 0
                
                # Format location string
                if lat != 0 and lon != 0:
                    location_str = f'{lat:.4f}°N, {lon:.4f}°E'
                elif row['location_name'] and row['location_name'] != 'Unknown Location':
                    location_str = row['location_name']
                elif row['city'] and row['city'] != 'Unknown':
                    location_str = f"{row['city']}, {row['country']}"
                else:
                    location_str = 'Malaysia (Location pending)'
                
                incident = {
                    'id': f"#ACC-{row['id']}",
                    'location': location_str,
                    'type': 'Road Accident',
                    'severity': row['severity'].capitalize() if row['severity'] else 'High',
                    'status': row['status'].replace('_', ' ').title() if row['status'] else 'Pending',
                    'timestamp': row['timestamp'] or '',
                    'lat': float(lat),
                    'lon': float(lon),
                    'confidence': float(row['confidence']) if row['confidence'] else 0
                }
                incidents.append(incident)
            
            return incidents
        except Exception as e:
            print(f"Error in fetch_incidents: {e}")
            return []
    
    try:
        # Use cache for performance
        incidents = get_cached('incidents', fetch_incidents)
        return jsonify({'incidents': incidents})
    except Exception as e:
        print(f"Error fetching incidents: {e}")
        return jsonify({'incidents': []})


@server.route('/api/notifications')
@login_required
def get_notifications():
    """API endpoint to get recent notifications"""
    def fetch_notifications():
        try:
            # Direct SQLite query for speed
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get recent alerts
            cursor.execute('''
                SELECT id, message, status, sent_at, language
                FROM Alert
                ORDER BY sent_at DESC
                LIMIT 10
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            # Format data for frontend
            notifications = []
            for row in rows:
                message = row['message'] or 'New alert'
                
                # Determine alert type based on status or message content
                alert_type = 'warning' if row['status'] == 'failed' else 'info'
                if 'critical' in message.lower():
                    alert_type = 'danger'
                elif 'high' in message.lower():
                    alert_type = 'warning'
                
                notification = {
                    'id': row['id'],
                    'message': message,
                    'type': alert_type,
                    'timestamp': row['sent_at'] or '',
                    'status': row['status'],
                    'language': row['language']
                }
                notifications.append(notification)
            
            return notifications
        except Exception as e:
            print(f"Error in fetch_notifications: {e}")
            return []
    
    try:
        # Use cache for performance
        notifications = get_cached('notifications', fetch_notifications)
        return jsonify({'notifications': notifications})
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return jsonify({'notifications': []})


@server.route('/api/users', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    """API endpoint to get all users or create a new user (Admin only)"""
    if request.method == 'GET':
        try:
            # Use direct SQLite connection
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, full_name, role, is_active, 
                       created_at, updated_at, phone, address, city, state, postal_code,
                       latitude, longitude
                FROM User 
                ORDER BY created_at DESC
            ''')
            
            users = cursor.fetchall()
            conn.close()
            
            users_data = [
                {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'role': user['role'],
                    'is_active': user['is_active'],
                    'created_at': user['created_at'],
                    'updated_at': user['updated_at'],
                    'phone': user['phone'],
                    'address': user['address'],
                    'city': user['city'],
                    'state': user['state'],
                    'postal_code': user['postal_code'],
                    'latitude': user['latitude'],
                    'longitude': user['longitude']
                }
                for user in users
            ]
            
            return jsonify({'users': users_data})
        except Exception as e:
            print(f"Error fetching users: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            # Hash the password
            password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Use direct SQLite connection
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get current timestamp
            from datetime import datetime
            now = datetime.utcnow().isoformat()
            
            cursor.execute('''
                INSERT INTO User (
                    username, email, password_hash, full_name, phone, address,
                    city, state, postal_code, latitude, longitude, role, is_active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['username'],
                data['email'],
                password_hash,
                data.get('full_name'),
                data.get('phone'),
                data.get('address'),
                data.get('city'),
                data.get('state'),
                data.get('postal_code'),
                data.get('latitude'),
                data.get('longitude'),
                data['role'],
                data.get('is_active', True),
                now,
                now
            ))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            return jsonify({
                'id': user_id,
                'username': data['username'],
                'email': data['email'],
                'full_name': data.get('full_name'),
                'phone': data.get('phone'),
                'address': data.get('address'),
                'city': data.get('city'),
                'state': data.get('state'),
                'postal_code': data.get('postal_code'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'role': data['role'],
                'is_active': data.get('is_active', True),
                'created_at': now
            }), 201
        except Exception as e:
            print(f"Error creating user: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 400


@server.route('/api/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@admin_required
def manage_user(user_id):
    """API endpoint to get, update, or delete a specific user (Admin only)"""
    if request.method == 'GET':
        try:
            # Use direct SQLite connection
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, full_name, phone, address, city, state, 
                       postal_code, latitude, longitude, role, is_active, 
                       created_at, updated_at
                FROM User 
                WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'phone': user['phone'],
                'address': user['address'],
                'city': user['city'],
                'state': user['state'],
                'postal_code': user['postal_code'],
                'latitude': user['latitude'],
                'longitude': user['longitude'],
                'role': user['role'],
                'is_active': user['is_active'],
                'created_at': user['created_at'],
                'updated_at': user['updated_at']
            })
        except Exception as e:
            print(f"Error fetching user: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.json
            
            # Use direct SQLite connection
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get current timestamp
            from datetime import datetime
            now = datetime.utcnow().isoformat()
            
            # Build update query
            if 'password' in data and data['password']:
                # Hash password if provided
                password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute('''
                    UPDATE User 
                    SET username = ?, email = ?, password_hash = ?, full_name = ?, 
                        phone = ?, address = ?, city = ?, state = ?, postal_code = ?,
                        latitude = ?, longitude = ?, role = ?, is_active = ?, updated_at = ?
                    WHERE id = ?
                ''', (
                    data['username'], data['email'], password_hash, data.get('full_name'),
                    data.get('phone'), data.get('address'), data.get('city'), data.get('state'),
                    data.get('postal_code'), data.get('latitude'), data.get('longitude'),
                    data['role'], data.get('is_active', True), now, user_id
                ))
            else:
                cursor.execute('''
                    UPDATE User 
                    SET username = ?, email = ?, full_name = ?, phone = ?, address = ?,
                        city = ?, state = ?, postal_code = ?, latitude = ?, longitude = ?,
                        role = ?, is_active = ?, updated_at = ?
                    WHERE id = ?
                ''', (
                    data['username'], data['email'], data.get('full_name'), data.get('phone'),
                    data.get('address'), data.get('city'), data.get('state'), data.get('postal_code'),
                    data.get('latitude'), data.get('longitude'), data['role'], 
                    data.get('is_active', True), now, user_id
                ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'id': user_id,
                'username': data['username'],
                'email': data['email'],
                'full_name': data.get('full_name'),
                'phone': data.get('phone'),
                'address': data.get('address'),
                'city': data.get('city'),
                'state': data.get('state'),
                'postal_code': data.get('postal_code'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'role': data['role'],
                'is_active': data.get('is_active', True),
                'updated_at': now
            })
        except Exception as e:
            print(f"Error updating user: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            # Use direct SQLite connection
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM User WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'User deleted successfully'})
        except Exception as e:
            print(f"Error deleting user: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 400


@server.route('/api/analytics')
@login_required
def get_analytics():
    """API endpoint to get analytics data"""
    # Optimized: Use direct SQLite queries instead of Prisma async operations
    try:
        print("🔄 Starting analytics fetch (optimized)...")
        
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all statistics in one go
        cursor.execute('SELECT COUNT(*) FROM Accident')
        total = cursor.fetchone()[0]
        
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM Accident WHERE timestamp >= ?', (week_ago,))
        week_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Accident WHERE severity = 'critical'")
        critical = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Accident WHERE status = 'resolved'")
        resolved = cursor.fetchone()[0]
        
        # Get accident details
        cursor.execute('''SELECT timestamp, city, location_name, severity, status
               FROM Accident 
               ORDER BY timestamp DESC 
               LIMIT 100''')
        rows = cursor.fetchall()
        accidents_raw = [dict(row) for row in rows]
        conn.close()
        
        print(f"✅ Analytics fetched: {total} total, {len(accidents_raw)} records retrieved")
        
        data = {
            'total': total,
            'week': week_count,
            'critical': critical,
            'resolved': resolved,
            'accidents': accidents_raw
        }
        
        # Process timeline data (last 30 days)
        timeline = []
        for i in range(30):
            date = (datetime.now() - timedelta(days=29-i)).strftime('%Y-%m-%d')
            # Raw SQL returns dicts with timestamp as string
            count = sum(1 for acc in data['accidents'] 
                       if acc.get('timestamp') and acc['timestamp'].startswith(date))
            timeline.append({'date': date, 'count': count})
        
        # Severity distribution
        severity = {
            'critical': sum(1 for acc in data['accidents'] if acc.get('severity') == 'critical'),
            'high': sum(1 for acc in data['accidents'] if acc.get('severity') == 'high'),
            'medium': sum(1 for acc in data['accidents'] if acc.get('severity') == 'medium'),
            'low': sum(1 for acc in data['accidents'] if acc.get('severity') == 'low')
        }
        
        # Hourly distribution - parse hour from timestamp string
        hourly = [0] * 24
        for acc in data['accidents']:
            timestamp_str = acc.get('timestamp')
            if timestamp_str:
                try:
                    # Parse timestamp string (format: YYYY-MM-DD HH:MM:SS)
                    hour = int(timestamp_str.split(' ')[1].split(':')[0])
                    if 0 <= hour < 24:
                        hourly[hour] += 1
                except Exception:
                    pass
        
        # Location distribution (top 10)
        location_counts = {}
        for acc in data['accidents']:
            loc = acc.get('city') or acc.get('location_name')
            if loc:
                location_counts[loc] = location_counts.get(loc, 0) + 1
        
        print(f"📍 Location counts: {location_counts}")
        
        locations = [
            {'location': loc, 'count': count}
            for loc, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        print(f"📍 Top 10 locations: {locations}")
        
        return jsonify({
            'stats': {
                'total': data['total'],
                'week': data['week'],
                'critical': data['critical'],
                'resolved': data['resolved']
            },
            'timeline': timeline,
            'severity': severity,
            'hourly': hourly,
            'locations': locations
        })
    except Exception as e:
        import traceback
        print(f"Error fetching analytics: {e}")
        print(traceback.format_exc())
        return jsonify({
            'stats': {'total': 0, 'week': 0, 'critical': 0, 'resolved': 0},
            'timeline': [],
            'severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'hourly': [0] * 24,
            'locations': []
        })


# OLD DASH APP - DISABLED IN FAVOR OF NEW HTML DASHBOARD
# The new dashboard is served via Flask routes: /dashboard, /dashboard/analytics, /dashboard/notifications
# Keeping this code commented for reference, but it's no longer active

# app = dash.Dash(
#     __name__,
#     server=server,
#     url_base_pathname='/old-dashboard/',  # Changed to avoid conflict
#     external_stylesheets=[
#         dbc.themes.BOOTSTRAP, 
#         dbc.icons.FONT_AWESOME,
#         'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@300;400;500;600;700;800&display=swap',
#         '/static/custom.css'
#     ],
#     suppress_callback_exceptions=True
# )

@server.route('/dashboard/notification-management')
@login_required
@admin_required
def notification_management_page():
    """Render notification management page (Admin only)"""
    return render_template('notification_management.html', user_role=current_user.role, username=current_user.username)


@server.route('/api/notification-config', methods=['GET', 'POST'])
@login_required
@admin_required
def notification_config():
    """API endpoint to get or update notification configuration (Admin only)"""
    if request.method == 'GET':
        # TODO: Fetch from database
        config = {
            'trigger_condition': 'severity-medium',
            'fallback_channel': 'sms',
            'language_priority': ['en', 'es', 'ar']
        }
        return jsonify(config)
    
    elif request.method == 'POST':
        try:
            data = request.json
            # TODO: Save to database
            print(f"Saving notification config: {data}")
            return jsonify({'success': True, 'message': 'Configuration saved successfully'})
        except Exception as e:
            print(f"Error saving notification config: {e}")
            return jsonify({'error': str(e)}), 500


@server.route('/api/notification-template', methods=['GET', 'POST'])
@login_required
@admin_required
def notification_template():
    """API endpoint to get or save notification templates (Admin only)"""
    if request.method == 'GET':
        template_name = request.args.get('template_name', 'collision-alert')
        # TODO: Fetch from database
        templates = {
            'collision-alert': '🚨 URGENT: Collision detected at {location}\n\nSeverity: {severity}\nTime: {timestamp}',
            'fire-detected': '🔥 FIRE ALERT: Fire detected at {location}',
            'medical-emergency': '🚑 MEDICAL EMERGENCY at {location}'
        }
        return jsonify({'template': templates.get(template_name, '')})
    
    elif request.method == 'POST':
        try:
            data = request.json
            # TODO: Save to database
            print(f"Saving notification template: {data['template_name']}")
            return jsonify({'success': True, 'message': 'Template saved successfully'})
        except Exception as e:
            print(f"Error saving notification template: {e}")
            return jsonify({'error': str(e)}), 500


@server.route('/api/notification-test', methods=['POST'])
@login_required
@admin_required
def notification_test():
    """API endpoint to send test notification (Admin only)"""
    try:
        data = request.json
        content = data.get('content', '')
        # TODO: Send actual test notification
        print(f"Sending test notification: {content[:100]}...")
        return jsonify({'success': True, 'message': 'Test notification sent successfully'})
    except Exception as e:
        print(f"Error sending test notification: {e}")
        return jsonify({'error': str(e)}), 500


@server.route('/dashboard/settings')
@login_required
def settings_page():
    """Render settings/preferences page"""
    # Get user's telegram bot token and chat ID if they are an emergency responder
    telegram_bot_token = None
    telegram_chat_id = None
    if current_user.role in ['admin', 'operator'] or current_user.username in ['police', 'ambulance', 'hospital']:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT telegram_bot_token, telegram_chat_id FROM User WHERE id = ?', (current_user.id,))
            result = cursor.fetchone()
            if result:
                telegram_bot_token = result[0]
                telegram_chat_id = result[1]
    
    return render_template('settings.html', 
                          user_role=current_user.role, 
                          username=current_user.username,
                          telegram_bot_token=telegram_bot_token,
                          telegram_chat_id=telegram_chat_id)


@server.route('/api/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    """API endpoint to get or update user settings"""
    if request.method == 'GET':
        # TODO: Fetch from database based on current_user.id
        default_settings = {
            'ui_language': 'en',
            'notification_language': 'en',
            'enable_notifications': True,
            'auto_logout_time': 15,
            'auto_logout_inactivity': False,
            'time_zone': 'UTC+08:00',
            'map_provider': 'openstreetmap',
            'dark_mode': False,
            'notification_channels': ['telegram', 'sms']
        }
        return jsonify({'settings': default_settings})
    
    elif request.method == 'POST':
        try:
            data = request.json
            # TODO: Save to database for current_user.id
            print(f"Saving user settings for user: {current_user.username}")
            print(f"Settings: {data}")
            
            # Save telegram_bot_token and telegram_chat_id if present (emergency responders only)
            if current_user.role in ['admin', 'operator'] or current_user.username in ['police', 'ambulance', 'hospital']:
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'database', 'roadsafenet.db')
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    if 'telegram_bot_token' in data and 'telegram_chat_id' in data:
                        cursor.execute('UPDATE User SET telegram_bot_token = ?, telegram_chat_id = ? WHERE id = ?', 
                                     (data['telegram_bot_token'], data['telegram_chat_id'], current_user.id))
                        print(f"Telegram bot token and chat ID updated for user {current_user.username}")
                    elif 'telegram_bot_token' in data:
                        cursor.execute('UPDATE User SET telegram_bot_token = ? WHERE id = ?', 
                                     (data['telegram_bot_token'], current_user.id))
                        print(f"Telegram bot token updated for user {current_user.username}")
                    elif 'telegram_chat_id' in data:
                        cursor.execute('UPDATE User SET telegram_chat_id = ? WHERE id = ?', 
                                     (data['telegram_chat_id'], current_user.id))
                        print(f"Telegram chat ID updated for user {current_user.username}")
                    
                    conn.commit()
            
            return jsonify({'success': True, 'message': 'Settings saved successfully'})
        except Exception as e:
            print(f"Error saving user settings: {e}")
            return jsonify({'error': str(e)}), 500


# ALL DASH CODE BELOW IS DISABLED - USING NEW HTML TEMPLATES INSTEAD
# The old Dash layout and callbacks are kept for reference but commented out

# app.layout = dbc.Container([
#     dcc.Location(id='url', refresh=False),
#     dcc.Interval(id='interval-component', interval=10000, n_intervals=0),
#     dbc.Navbar(...),
#     html.Div(id='page-content'),
# ], fluid=True)


# ALL OLD DASH LAYOUT FUNCTIONS COMMENTED OUT - NOT NEEDED WITH NEW HTML TEMPLATES

# def create_home_layout():
#     """Old Dash home layout"""
#     pass

# def create_incidents_layout():
#     """Old Dash incidents layout"""
#     pass

# def create_analytics_layout():
#     """Old Dash analytics layout"""
#     pass

# ALL OLD DASH CALLBACKS COMMENTED OUT - NOT NEEDED WITH NEW HTML TEMPLATES

# @app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
# def display_page(pathname):
#     pass

# @app.callback([Output('total-accidents', 'children'), ...], Input('interval-component', 'n_intervals'))
# def update_statistics(n):
#     pass


if __name__ == '__main__':
    # Initialize video stream but DON'T start automatically
    from utils.video_stream import get_video_stream
    video_stream = get_video_stream()
    print("🎥 Video stream initialized - Waiting for user to start monitoring...")
    
    server.run(
        host=Config.DASH_HOST,
        port=Config.DASH_PORT,
        debug=Config.DEBUG
    )
