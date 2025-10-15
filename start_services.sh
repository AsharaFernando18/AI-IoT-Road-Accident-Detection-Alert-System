#!/bin/bash

# RoadSafeNet - Service Startup Script
# This script starts all services required for the system

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if database exists
if [ ! -f "database/roadsafenet.db" ]; then
    echo -e "${RED}Database not found! Please run: python database/init_db.py${NC}"
    exit 1
fi

# Check if YOLO model exists
if [ ! -f "ai_model/models/yolov10n.pt" ]; then
    echo -e "${RED}YOLO model not found! Please download it first.${NC}"
    exit 1
fi

echo -e "${GREEN}Starting RoadSafeNet Services...${NC}"
echo ""

# Function to handle termination
cleanup() {
    echo -e "\n${YELLOW}Stopping all services...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if running in terminal
if [ -t 0 ]; then
    echo -e "${GREEN}Starting services in background...${NC}"
    echo ""
    
    # Start API server
    echo -e "${YELLOW}[1/2] Starting FastAPI Backend on http://localhost:8000${NC}"
    python backend/api.py &
    API_PID=$!
    sleep 3
    
    # Start Dashboard
    echo -e "${YELLOW}[2/2] Starting Dashboard on http://localhost:8050/dashboard/${NC}"
    python frontend/app.py &
    DASH_PID=$!
    sleep 3
    
    echo ""
    echo -e "${GREEN}=================================${NC}"
    echo -e "${GREEN}   RoadSafeNet Services Running  ${NC}"
    echo -e "${GREEN}=================================${NC}"
    echo ""
    echo -e "📊 Dashboard: ${GREEN}http://localhost:8050/dashboard/${NC}"
    echo -e "🔌 API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "👤 Login:     username=${GREEN}admin${NC}, password=${GREEN}admin123${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""
    
    # Wait for both services
    wait $API_PID $DASH_PID
else
    # Non-interactive mode (for process managers)
    python backend/api.py &
    python frontend/app.py &
    wait
fi
