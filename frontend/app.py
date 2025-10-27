"""
Flask Application with Plotly Dash Integration
Main dashboard for RoadSafeNet
"""

from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
import sys
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import pandas as pd
import threading

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
        async def get_user():
            if not db.is_connected():
                await db.connect()
            user_data = await db.user.find_unique(where={"id": int(user_id)})
            return user_data

        user_data = run_in_background(get_user())
        return User(user_data) if user_data else None
    except Exception as e:
        print(f"Error loading user: {e}")
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
        
        async def authenticate():
            if not db.is_connected():
                await db.connect()
            user_data = await db.user.find_unique(where={"username": username})
            return user_data
        
        user_data = run_in_background(authenticate())
        
        if user_data:
            # Check password using bcrypt
            password_bytes = password.encode('utf-8')
            hash_bytes = user_data.password_hash.encode('utf-8')
            password_match = bcrypt.checkpw(password_bytes, hash_bytes)
            
            if password_match:
                if user_data.is_active:
                    user = User(user_data)
                    # Don't use remember_me - session will expire when browser closes or after timeout
                    login_user(user, remember=False)
                    session.permanent = False  # Session ends when browser closes
                    return redirect('/dashboard')
                else:
                    flash('Account is inactive', 'danger')
            else:
                flash('Invalid username or password', 'danger')
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')


@server.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    session.clear()  # Clear all session data
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))


@server.route('/dashboard')
@server.route('/dashboard/')
@login_required
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')


@server.route('/dashboard/analytics')
@server.route('/dashboard/analytics/')
@login_required
def analytics():
    """Analytics page"""
    return render_template('analytics.html')


@server.route('/dashboard/notifications')
@server.route('/dashboard/notifications/')
@login_required
def notifications_page():
    """Notifications management page"""
    return render_template('notifications.html')


@server.route('/api/incidents')
@login_required
def get_incidents():
    """API endpoint to get active incidents"""
    async def fetch_incidents():
        if not db.is_connected():
            await db.connect()
        
        # Get recent accidents
        accidents = await db.accident.find_many(
            where={'status': {'not': 'RESOLVED'}},
            take=10,
            order={'timestamp': 'desc'}
        )
        
        return accidents
    
    try:
        accidents = run_in_background(fetch_incidents())
        
        # Format data for frontend
        incidents = []
        for acc in accidents:
            incident = {
                'id': f'Incident #{acc.id}',
                'location': f'{acc.latitude:.4f}°N, {acc.longitude:.4f}°E' if acc.latitude and acc.longitude else 'Unknown',
                'type': acc.accident_type or 'Collision',
                'severity': acc.severity.capitalize() if acc.severity else 'High',
                'status': acc.status.replace('_', ' ').title() if acc.status else 'En Route',
                'timestamp': acc.timestamp.strftime('%Y-%m-%d %H:%M:%S') if acc.timestamp else ''
            }
            incidents.append(incident)
        
        return jsonify({'incidents': incidents})
    except Exception as e:
        print(f"Error fetching incidents: {e}")
        return jsonify({'incidents': []})


@server.route('/api/notifications')
@login_required
def get_notifications():
    """API endpoint to get recent notifications"""
    async def fetch_notifications():
        if not db.is_connected():
            await db.connect()
        
        # Get recent alerts
        alerts = await db.alert.find_many(
            take=10,
            order={'sent_at': 'desc'}
        )
        
        return alerts
    
    try:
        alerts = run_in_background(fetch_notifications())
        
        # Format data for frontend
        notifications = []
        for alert in alerts:
            notification = {
                'id': alert.id,
                'message': alert.message or 'New alert',
                'type': alert.alert_type or 'info',
                'timestamp': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S') if alert.timestamp else ''
            }
            notifications.append(notification)
        
        return jsonify({'notifications': notifications})
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return jsonify({'notifications': []})


@server.route('/api/analytics')
@login_required
def get_analytics():
    """API endpoint to get analytics data"""
    async def fetch_analytics():
        if not db.is_connected():
            await db.connect()
        
        # Get statistics
        total = await db.accident.count()
        
        # Last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        week_count = await db.accident.count(where={"timestamp": {"gte": week_ago}})
        
        # Critical incidents
        critical = await db.accident.count(where={"severity": "critical"})
        
        # Resolved incidents
        resolved = await db.accident.count(where={"status": "resolved"})
        
        # Get all accidents for timeline
        accidents = await db.accident.find_many(
            order={'timestamp': 'desc'},
            take=100
        )
        
        return {
            'total': total,
            'week': week_count,
            'critical': critical,
            'resolved': resolved,
            'accidents': accidents
        }
    
    try:
        data = run_in_background(fetch_analytics())
        
        # Process timeline data (last 30 days)
        timeline = []
        for i in range(30):
            date = (datetime.now() - timedelta(days=29-i)).strftime('%Y-%m-%d')
            count = sum(1 for acc in data['accidents'] if acc.timestamp and acc.timestamp.strftime('%Y-%m-%d') == date)
            timeline.append({'date': date, 'count': count})
        
        # Severity distribution
        severity = {
            'critical': sum(1 for acc in data['accidents'] if acc.severity == 'critical'),
            'high': sum(1 for acc in data['accidents'] if acc.severity == 'high'),
            'medium': sum(1 for acc in data['accidents'] if acc.severity == 'medium'),
            'low': sum(1 for acc in data['accidents'] if acc.severity == 'low')
        }
        
        # Hourly distribution
        hourly = [0] * 24
        for acc in data['accidents']:
            if acc.timestamp:
                hour = acc.timestamp.hour
                hourly[hour] += 1
        
        # Location distribution (top 10)
        location_counts = {}
        for acc in data['accidents']:
            if hasattr(acc, 'location') and acc.location:
                loc = acc.location.city or 'Unknown'
                location_counts[loc] = location_counts.get(loc, 0) + 1
        
        locations = [
            {'location': loc, 'count': count}
            for loc, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
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
        print(f"Error fetching analytics: {e}")
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
    server.run(
        host=Config.DASH_HOST,
        port=Config.DASH_PORT,
        debug=Config.DEBUG
    )
