#!/bin/bash
# M2 Video Metadata Service - Local Run Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}M2 Video Metadata Service - Starting...${NC}"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}Python version: $PYTHON_VERSION${NC}"

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}Error: FFmpeg is not installed${NC}"
    echo -e "${YELLOW}Install FFmpeg:${NC}"
    echo "  macOS:   brew install ffmpeg"
    echo "  Ubuntu:  sudo apt-get install ffmpeg"
    echo "  Windows: choco install ffmpeg"
    exit 1
fi

FFMPEG_VERSION=$(ffmpeg -version | head -n1)
echo -e "${GREEN}FFmpeg: $FFMPEG_VERSION${NC}"

# Check environment variables
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo -e "${YELLOW}Warning: GOOGLE_APPLICATION_CREDENTIALS not set${NC}"
    echo -e "${YELLOW}For local development, set:${NC}"
    echo "  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json"
fi

# Load .env if exists
if [ -f .env ]; then
    echo -e "${GREEN}Loading .env file...${NC}"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${GREEN}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Run tests (optional, comment out for faster startup)
if [ "$1" = "--test" ]; then
    echo -e "${GREEN}Running tests...${NC}"
    pytest tests/ -v --cov=app --cov-report=term-missing
fi

# Start server
echo -e "${GREEN}Starting Flask server on port ${PORT:-8002}...${NC}"
echo -e "${YELLOW}Health check: http://localhost:${PORT:-8002}/health${NC}"
echo -e "${YELLOW}API docs: See README.md${NC}"
echo ""

python -m app.api
