# 🚀 RoadSafeNet Quick Start Guide

Get RoadSafeNet up and running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.8 or higher
- ✅ pip package manager
- ✅ 4GB+ free RAM
- ✅ 10GB+ free disk space

## Step 1: Download & Setup (2 minutes)

### Option A: Automated Setup (Linux/macOS)
```bash
# Clone repository
git clone https://github.com/AsharaFernando18/AI-IoT-Road-Accident-Detection-Alert-System.git
cd AI-IoT-Road-Accident-Detection-Alert-System

# Run setup script
chmod +x setup.sh
./setup.sh
```

### Option B: Automated Setup (Windows)
```bash
# Clone repository
git clone https://github.com/AsharaFernando18/AI-IoT-Road-Accident-Detection-Alert-System.git
cd AI-IoT-Road-Accident-Detection-Alert-System

# Run setup script
setup.bat
```

### Option C: Manual Setup
```bash
# Clone repository
git clone https://github.com/AsharaFernando18/AI-IoT-Road-Accident-Detection-Alert-System.git
cd AI-IoT-Road-Accident-Detection-Alert-System

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install and generate Prisma
pip install prisma
prisma generate --schema=database/schema.prisma

# Setup environment
cp .env.example .env

# Initialize database
python database/init_db.py
```

## Step 2: Configure Telegram Bot (1 minute)

1. **Create a Telegram Bot:**
   - Open Telegram, search for `@BotFather`
   - Send `/newbot` command
   - Follow instructions to name your bot
   - Copy the bot token

2. **Get Your Chat ID:**
   - Search for `@userinfobot` in Telegram
   - Start chat and it will show your chat ID

3. **Update .env file:**
   ```bash
   # Edit .env file
   nano .env  # or use any text editor
   
   # Update these lines:
   TELEGRAM_BOT_TOKEN="your_bot_token_here"
   TELEGRAM_CHAT_IDS="your_chat_id_here"
   ```

## Step 3: Test Components (1 minute)

```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run component tests
python tests/test_components.py
```

You should see:
- ✅ Configuration OK
- ✅ Detector initialized
- ✅ Geolocation service OK
- ✅ Translation service loaded
- ✅ Telegram bot initialized

## Step 4: Start the System (1 minute)

### Terminal 1: Start Web Dashboard
```bash
source venv/bin/activate
python frontend/app.py
```
Dashboard will be available at: **http://localhost:8050**

### Terminal 2: Start API Server
```bash
source venv/bin/activate
python backend/api.py
```
API docs available at: **http://localhost:8000/docs**

### Terminal 3: Start Detection System (Optional for testing)
```bash
source venv/bin/activate
python main.py
```

## Step 5: Access the Dashboard

1. **Open your browser:** http://localhost:8050/dashboard/
2. **Login with default credentials:**
   - Username: `admin`
   - Password: `admin123`

## Quick Testing

### Test with Webcam
1. Update `.env`:
   ```bash
   VIDEO_SOURCE="0"
   ```

2. Run detection:
   ```bash
   python main.py
   ```

3. Press 'q' to quit

### Test with Sample Video
1. Download a sample video or use your own
2. Update `.env`:
   ```bash
   VIDEO_SOURCE="/path/to/your/video.mp4"
   ```

3. Run detection:
   ```bash
   python main.py
   ```

## Common Issues & Solutions

### Issue: "Module not found" error
**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Issue: Prisma errors
**Solution:**
```bash
# Regenerate Prisma client
prisma generate --schema=database/schema.prisma
```

### Issue: Telegram bot not working
**Solution:**
1. Verify token is correct in `.env`
2. Ensure bot token has no extra spaces
3. Test with: `python telegram_bot/bot.py`

### Issue: Database errors
**Solution:**
```bash
# Reset database
python database/init_db.py reset
python database/init_db.py
```

### Issue: YOLO model not found
**Solution:**
```bash
# Download default model
python -c "from ultralytics import YOLO; YOLO('yolov10n.pt')"
mv yolov10n.pt ai_model/models/
```

## Next Steps

### 1. Explore the Dashboard
- 📊 View statistics on home page
- 🚦 Check incidents page
- 📈 Analyze trends in analytics
- ⚙️ Configure settings

### 2. Configure Detection Settings
Edit `.env` to adjust:
```bash
YOLO_CONFIDENCE_THRESHOLD=0.5  # Lower = more detections
VIDEO_FRAME_SKIP=2             # Higher = faster but less accurate
```

### 3. Customize Alert Templates
Access dashboard → Notifications → Edit templates

### 4. Add Users
Access dashboard → Users → Add new user

### 5. Set Up Real CCTV Stream
Update `.env` with RTSP URL:
```bash
VIDEO_SOURCE="rtsp://username:password@camera-ip:554/stream"
```

## Useful Commands

```bash
# Check service status
python tests/test_components.py

# View logs
tail -f logs/roadsafenet.log

# Backup database
cp database/roadsafenet.db database/backup_$(date +%Y%m%d).db

# Update system
git pull
pip install -r requirements.txt --upgrade
prisma generate --schema=database/schema.prisma
```

## API Quick Reference

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Get Statistics
```bash
curl http://localhost:8000/api/analytics/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Accidents
```bash
curl http://localhost:8000/api/accidents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Performance Tips

### For Better Performance:
1. **Use GPU** if available (CUDA-enabled)
2. **Increase FRAME_SKIP** for faster processing
3. **Lower CONFIDENCE_THRESHOLD** for more detections
4. **Use smaller YOLO model** (yolov10n is fastest)

### For Better Accuracy:
1. **Use larger YOLO model** (yolov10l or yolov10x)
2. **Decrease FRAME_SKIP** to process more frames
3. **Increase CONFIDENCE_THRESHOLD** to reduce false positives

## Getting Help

- 📖 **Full Documentation:** [README.md](../README.md)
- 🔧 **Deployment Guide:** [docs/DEPLOYMENT.md](DEPLOYMENT.md)
- 🌐 **API Documentation:** [docs/API.md](API.md)
- 🐛 **Report Issues:** [GitHub Issues](https://github.com/AsharaFernando18/AI-IoT-Road-Accident-Detection-Alert-System/issues)

## Video Walkthrough

Coming soon! Check the repository for video tutorials.

---

**Congratulations! 🎉**

You've successfully set up RoadSafeNet! Start detecting accidents and making roads safer.

**Remember to:**
- ⚠️ Change default passwords in production
- 🔒 Keep your `.env` file secure
- 📝 Monitor logs regularly
- 💾 Backup database frequently

Happy monitoring! 🚨
