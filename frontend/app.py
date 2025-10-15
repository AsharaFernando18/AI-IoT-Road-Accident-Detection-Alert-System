"""
Flask Application with Plotly Dash Integration
Main dashboard for RoadSafeNet
"""

from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
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

sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from prisma import Prisma

# Initialize Flask app
server = Flask(__name__, 
              template_folder=str(Config.TEMPLATES_DIR),
              static_folder=str(Config.STATIC_DIR))
server.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = 'login'

# Database
db = Prisma()


class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, user_data):
        self.id = user_data.id
        self.username = user_data.username
        self.email = user_data.email
        self.role = user_data.role
        self.is_active = user_data.is_active


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def get_user():
        await db.connect()
        user_data = await db.user.find_unique(where={"id": int(user_id)})
        await db.disconnect()
        return user_data
    
    user_data = loop.run_until_complete(get_user())
    return User(user_data) if user_data else None


# Flask Routes
@server.route('/')
def index():
    """Redirect to login or dashboard"""
    if current_user.is_authenticated:
        return redirect('/dashboard')
    return redirect(url_for('login'))


@server.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        async def authenticate():
            await db.connect()
            user_data = await db.user.find_unique(where={"username": username})
            await db.disconnect()
            return user_data
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        user_data = loop.run_until_complete(authenticate())
        
        if user_data and check_password_hash(user_data.password_hash, password):
            if user_data.is_active:
                user = User(user_data)
                login_user(user)
                return redirect('/dashboard')
            else:
                flash('Account is inactive', 'danger')
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')


@server.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return redirect(url_for('login'))


# Initialize Dash app
app = dash.Dash(
    __name__,
    server=server,
    url_base_pathname='/dashboard/',
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True
)

# Dash Layout
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dcc.Interval(id='interval-component', interval=10000, n_intervals=0),  # Update every 10 seconds
    
    # Navbar
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("🚨 RoadSafeNet", className="ms-2"),
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Dashboard", href="/dashboard/")),
                dbc.NavItem(dbc.NavLink("Incidents", href="/dashboard/incidents")),
                dbc.NavItem(dbc.NavLink("Analytics", href="/dashboard/analytics")),
                dbc.NavItem(dbc.NavLink("Notifications", href="/dashboard/notifications")),
                dbc.NavItem(dbc.NavLink("Users", href="/dashboard/users")),
                dbc.NavItem(dbc.NavLink("Logs", href="/dashboard/logs")),
                dbc.NavItem(dbc.NavLink("Settings", href="/dashboard/settings")),
                dbc.NavItem(dbc.NavLink("Logout", href="/logout")),
            ], navbar=True)
        ], fluid=True),
        color="dark",
        dark=True,
        className="mb-4"
    ),
    
    # Main content
    html.Div(id='page-content'),
    
], fluid=True, style={'backgroundColor': '#f8f9fa'})


# Home Dashboard Layout
def create_home_layout():
    """Create home dashboard layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("🏠 Dashboard Overview", className="mb-4"),
            ], width=12)
        ]),
        
        # Statistics Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Total Accidents", className="card-title"),
                        html.H2(id="total-accidents", className="text-primary"),
                        html.P("All time", className="text-muted")
                    ])
                ], className="shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Pending", className="card-title"),
                        html.H2(id="pending-accidents", className="text-warning"),
                        html.P("Awaiting response", className="text-muted")
                    ])
                ], className="shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Last 24h", className="card-title"),
                        html.H2(id="recent-accidents", className="text-info"),
                        html.P("Recent detections", className="text-muted")
                    ])
                ], className="shadow-sm")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Alerts Sent", className="card-title"),
                        html.H2(id="total-alerts", className="text-success"),
                        html.P("Total notifications", className="text-muted")
                    ])
                ], className="shadow-sm")
            ], md=3),
        ], className="mb-4"),
        
        # Charts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 Accident Timeline (Last 7 Days)"),
                    dbc.CardBody([
                        dcc.Graph(id="timeline-chart")
                    ])
                ], className="shadow-sm")
            ], md=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📈 Severity Distribution"),
                    dbc.CardBody([
                        dcc.Graph(id="severity-chart")
                    ])
                ], className="shadow-sm")
            ], md=4),
        ], className="mb-4"),
        
        # Map
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🗺️ Accident Heatmap"),
                    dbc.CardBody([
                        dcc.Graph(id="accident-map")
                    ])
                ], className="shadow-sm")
            ], md=12),
        ]),
        
    ], fluid=True)


# Incidents Page Layout
def create_incidents_layout():
    """Create incidents page layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("🚦 Recent Incidents", className="mb-4"),
            ], width=12)
        ]),
        
        # Filters
        dbc.Row([
            dbc.Col([
                dbc.Label("Severity"),
                dcc.Dropdown(
                    id='severity-filter',
                    options=[
                        {'label': 'All', 'value': 'all'},
                        {'label': 'Low', 'value': 'low'},
                        {'label': 'Medium', 'value': 'medium'},
                        {'label': 'High', 'value': 'high'},
                        {'label': 'Critical', 'value': 'critical'}
                    ],
                    value='all'
                )
            ], md=3),
            
            dbc.Col([
                dbc.Label("Status"),
                dcc.Dropdown(
                    id='status-filter',
                    options=[
                        {'label': 'All', 'value': 'all'},
                        {'label': 'Pending', 'value': 'pending'},
                        {'label': 'Confirmed', 'value': 'confirmed'},
                        {'label': 'False Alarm', 'value': 'false_alarm'},
                        {'label': 'Resolved', 'value': 'resolved'}
                    ],
                    value='all'
                )
            ], md=3),
        ], className="mb-4"),
        
        # Incidents Table
        dbc.Row([
            dbc.Col([
                html.Div(id="incidents-table")
            ], width=12)
        ]),
        
    ], fluid=True)


# Analytics Page Layout
def create_analytics_layout():
    """Create analytics page layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("📊 Analytics Dashboard", className="mb-4"),
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📈 Accidents by Hour of Day"),
                    dbc.CardBody([
                        dcc.Graph(id="hourly-chart")
                    ])
                ], className="shadow-sm")
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📅 Accidents by Day of Week"),
                    dbc.CardBody([
                        dcc.Graph(id="weekly-chart")
                    ])
                ], className="shadow-sm")
            ], md=6),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🌍 Accidents by City"),
                    dbc.CardBody([
                        dcc.Graph(id="city-chart")
                    ])
                ], className="shadow-sm")
            ], md=12),
        ]),
        
    ], fluid=True)


# Callbacks for routing
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """Route to different pages"""
    if pathname == '/dashboard/' or pathname == '/dashboard':
        return create_home_layout()
    elif pathname == '/dashboard/incidents':
        return create_incidents_layout()
    elif pathname == '/dashboard/analytics':
        return create_analytics_layout()
    elif pathname == '/dashboard/notifications':
        return html.H2("🔔 Notifications Management - Coming Soon")
    elif pathname == '/dashboard/users':
        return html.H2("👥 User Management - Coming Soon")
    elif pathname == '/dashboard/logs':
        return html.H2("📝 System Logs - Coming Soon")
    elif pathname == '/dashboard/settings':
        return html.H2("⚙️ Settings - Coming Soon")
    else:
        return create_home_layout()


# Callback for updating statistics
@app.callback(
    [Output('total-accidents', 'children'),
     Output('pending-accidents', 'children'),
     Output('recent-accidents', 'children'),
     Output('total-alerts', 'children')],
    Input('interval-component', 'n_intervals')
)
def update_statistics(n):
    """Update statistics cards"""
    async def get_stats():
        await db.connect()
        
        total = await db.accident.count()
        pending = await db.accident.count(where={"status": "pending"})
        
        yesterday = datetime.now() - timedelta(days=1)
        recent = await db.accident.count(where={"timestamp": {"gte": yesterday}})
        
        alerts = await db.alert.count()
        
        await db.disconnect()
        return total, pending, recent, alerts
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        stats = loop.run_until_complete(get_stats())
        return str(stats[0]), str(stats[1]), str(stats[2]), str(stats[3])
    except:
        return "0", "0", "0", "0"


if __name__ == '__main__':
    server.run(
        host=Config.DASH_HOST,
        port=Config.DASH_PORT,
        debug=Config.DEBUG
    )
