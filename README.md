# 🚨 RoadSafeNet - AI-Powered Road Accident Detection System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![YOLOv10](https://img.shields.io/badge/YOLOv10-Ultralytics-yellow.svg)](https://github.com/ultralytics/ultralytics)

> An open-source, AI-powered road accident detection and alert system using YOLOv10, multilingual NLP, and IoT integration.

## 🎯 Overview

**RoadSafeNet** is a comprehensive road safety system that:
- 🎥 Detects accidents in real-time from CCTV streams using **YOLOv10**
- 📍 Identifies exact locations using **OpenStreetMap + Nominatim API**
- 🌍 Sends multilingual alerts (English, Spanish, Arabic, Hindi, Mandarin) via **Telegram**
- 📊 Provides analytics dashboards with **Plotly & Dash**
- 💾 Stores data in **SQLite** with **Prisma ORM**

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  CCTV Stream    │─────→│  YOLOv10 Model   │─────→│  Accident DB    │
│  (Video Input)  │      │  (Detection)     │      │  (SQLite)       │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │                          │
                                  ↓                          ↓
                         ┌─────────────────┐      ┌─────────────────┐
                         │  Geolocation    │      │  Alert System   │
                         │  (Nominatim)    │      │  (Telegram)     │
                         └─────────────────┘      └─────────────────┘
                                  │                          │
                                  ↓                          ↓
                         ┌──────────────────────────────────────┐
                         │  Multilingual Translation (mBART)    │
                         └──────────────────────────────────────┘
                                           │
                                           ↓
                         ┌──────────────────────────────────────┐
                         │  Web Dashboard (Flask + Plotly Dash) │
                         └──────────────────────────────────────┘
```

## ✨ Features

### Core Functionality
- ✅ Real-time accident detection with ≥94% accuracy (YOLOv10)
- ✅ GPS coordinate extraction and reverse geocoding
- ✅ Multilingual alert generation (5 languages)
- ✅ Telegram bot integration for instant notifications
- ✅ Web-based dashboard for monitoring and analytics
- ✅ RESTful API with Swagger documentation
- ✅ Role-based access control (Admin, Operator, Viewer)
- ✅ System logging and audit trails

### Advanced Features
- 📊 Interactive analytics with heatmaps
- 📈 Accident trend analysis
- 🗺️ Location-based severity mapping
- 🔔 Customizable alert templates
- 👥 Multi-user support
- ⚙️ Configurable detection thresholds

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Node.js (for Prisma)
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/AsharaFernando18/AI-IoT-Road-Accident-Detection-Alert-System.git
cd AI-IoT-Road-Accident-Detection-Alert-System
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install Prisma**
```bash
pip install prisma
prisma generate --schema=database/schema.prisma
```

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration (Telegram bot token, etc.)
```

6. **Initialize database**
```bash
python database/init_db.py
```

7. **Run the application**
```bash
# Start the detection system
python main.py

# In a separate terminal, start the web dashboard
python frontend/app.py

# In another terminal, start the API server
python backend/api.py
```

## 📁 Project Structure

```
AI-IoT-Road-Accident-Detection-Alert-System/
├── ai_model/                  # AI/ML components
│   ├── detector.py           # YOLOv10 accident detection
│   └── models/               # Model weights (download separately)
├── backend/                   # Backend API
│   └── api.py                # FastAPI REST endpoints
├── frontend/                  # Web dashboard
│   ├── app.py                # Flask + Dash application
│   ├── templates/            # HTML templates
│   │   └── login.html        # Login page
│   └── static/               # Static assets
├── database/                  # Database layer
│   ├── schema.prisma         # Prisma schema definition
│   ├── init_db.py            # Database initialization
│   └── roadsafenet.db        # SQLite database (created)
├── telegram_bot/             # Telegram integration
│   └── bot.py                # Telegram alert service
├── utils/                     # Utility modules
│   ├── geolocation.py        # Nominatim API wrapper
│   └── translation.py        # Multilingual translation
├── logs/                      # Application logs
├── uploads/                   # Uploaded/detected images
├── config.py                  # Configuration management
├── main.py                    # Main orchestrator
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL="file:./database/roadsafenet.db"

# Telegram Bot
TELEGRAM_BOT_TOKEN="your_bot_token_from_botfather"
TELEGRAM_CHAT_IDS="123456789,987654321"

# OpenStreetMap
NOMINATIM_USER_AGENT="RoadSafeNet/1.0"

# YOLOv10 Model
YOLO_MODEL_PATH="ai_model/models/yolov10n.pt"
YOLO_CONFIDENCE_THRESHOLD=0.5

# Security
SECRET_KEY="change-this-in-production"
JWT_SECRET_KEY="change-this-in-production"

# Video Source (0 for webcam, or path/URL)
VIDEO_SOURCE="0"
```

### Getting a Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Copy the bot token to your `.env` file
4. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)

## 📊 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | User authentication |
| `/api/accidents` | GET | List all accidents |
| `/api/accidents` | POST | Create accident record |
| `/api/accidents/{id}` | GET | Get accident details |
| `/api/analytics/stats` | GET | System statistics |
| `/api/analytics/heatmap` | GET | Location heatmap data |
| `/api/alerts` | GET | List alerts |
| `/api/users` | GET | List users (admin) |
| `/api/logs` | GET | System logs |
| `/api/settings` | GET/PATCH | System settings |

## 🖥️ Web Dashboard

Access the dashboard at: **http://localhost:8050/dashboard/**

### Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

### Dashboard Pages

1. **🏠 Home** - Overview statistics, timeline, heatmap
2. **🚦 Incidents** - List of detected accidents with filters
3. **📊 Analytics** - Charts and trend analysis
4. **🔔 Notifications** - Alert management
5. **👥 Users** - User management (admin only)
6. **📝 Logs** - System logs viewer
7. **⚙️ Settings** - System configuration

## 🧪 Testing

### Test Individual Components

```bash
# Test accident detector
python ai_model/detector.py

# Test geolocation service
python utils/geolocation.py

# Test translation service
python utils/translation.py

# Test Telegram bot
python telegram_bot/bot.py
```

### Sample Video Testing

Place your test video in the project root and update `.env`:
```bash
VIDEO_SOURCE="path/to/your/test_video.mp4"
```

## 🗄️ Database Schema

### Main Tables

- **users** - User accounts with roles
- **accidents** - Detected accident records
- **alerts** - Sent notifications
- **alert_templates** - Multilingual message templates
- **system_logs** - Application logs
- **system_settings** - Configuration
- **emergency_contacts** - Alert recipients

## 🌍 Supported Languages

| Language | Code | Translation |
|----------|------|-------------|
| English | en | mBART-50 |
| Spanish | es | mBART-50 |
| Arabic | ar | mBART-50 |
| Hindi | hi | mBART-50 |
| Mandarin | zh | mBART-50 |

## 📈 Performance

- **Detection Speed**: ~30 FPS (GPU), ~5 FPS (CPU)
- **Accuracy**: ≥94% on test dataset
- **Alert Latency**: <2 seconds
- **Translation Time**: ~1 second per language

## 🛠️ Deployment

### Production Considerations

1. **Change default secrets** in `.env`
2. **Use HTTPS** for API and dashboard
3. **Configure firewall** rules
4. **Set up process manager** (systemd, supervisor)
5. **Enable database backups**
6. **Use reverse proxy** (nginx, Apache)
7. **Monitor system logs**

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Ultralytics** for YOLOv10
- **OpenStreetMap** for geocoding services
- **Hugging Face** for transformer models
- **Telegram** for bot API
- **FastAPI** and **Plotly** communities

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/AsharaFernando18/AI-IoT-Road-Accident-Detection-Alert-System/issues)

## 🗺️ Roadmap

- [ ] Mobile app (React Native)
- [ ] Voice alerts (gTTS integration)
- [ ] Weather API integration
- [ ] Multi-camera support
- [ ] Cloud deployment guides
- [ ] Docker Compose setup

---

**Made with ❤️ for road safety**

*Star ⭐ this repository if you find it useful!*