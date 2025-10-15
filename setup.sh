#!/bin/bash

# RoadSafeNet Setup Script
# Automated installation for Linux/macOS

echo "========================================="
echo "🚨 RoadSafeNet Setup Script"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "✓ Virtual environment created and activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "✓ Python dependencies installed"

# Install Prisma
echo ""
echo "Installing Prisma..."
pip install prisma
echo "✓ Prisma installed"

# Generate Prisma client
echo ""
echo "Generating Prisma client..."
prisma generate --schema=database/schema.prisma
echo "✓ Prisma client generated"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "⚠️  Please edit .env with your configuration!"
else
    echo ""
    echo "✓ .env file already exists"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p logs uploads ai_model/models cache/huggingface
echo "✓ Directories created"

# Initialize database
echo ""
echo "Initializing database..."
python database/init_db.py
echo "✓ Database initialized"

# Download YOLOv10 model (optional)
echo ""
read -p "Do you want to download YOLOv10 model now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Downloading YOLOv10n model..."
    python -c "from ultralytics import YOLO; YOLO('yolov10n.pt')"
    mv yolov10n.pt ai_model/models/
    echo "✓ Model downloaded"
fi

echo ""
echo "========================================="
echo "✅ Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Configure your .env file with Telegram bot token"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the application:"
echo "   - Detection: python main.py"
echo "   - Dashboard: python frontend/app.py"
echo "   - API: python backend/api.py"
echo ""
echo "Documentation: README.md"
echo "========================================="
