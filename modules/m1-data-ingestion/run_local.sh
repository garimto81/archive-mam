#!/bin/bash
# Local development quick start script for M1 Data Ingestion Service

set -e

echo "🚀 M1 Data Ingestion Service - Local Development"
echo "================================================"

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "❌ Python 3.11+ required"; exit 1; }

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Copy environment variables
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your GCP credentials"
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Available commands:"
echo "  - Run tests:      pytest tests/ -v"
echo "  - Run server:     python -m app.api"
echo "  - Run coverage:   pytest tests/ --cov=app --cov-report=html"
echo ""
echo "🌐 Server will run at: http://localhost:8001"
echo ""

# Ask if user wants to run server
read -p "Start Flask server now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting server..."
    python -m app.api
fi
