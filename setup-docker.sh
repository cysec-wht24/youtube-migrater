#!/bin/bash
# Quick Setup Script for YouTube Migrator Docker

echo "🎬 YouTube Migrator Docker Setup"
echo "================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker is installed"
echo ""

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  Docker Compose is not installed (optional)"
    echo "   You can still use Docker commands directly"
else
    echo "✅ Docker Compose is installed"
fi
echo ""

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
    echo "✅ Data directory created"
else
    echo "✅ Data directory already exists"
fi
echo ""

# Check for client_secret.json
if [ ! -f "data/client_secret.json" ]; then
    echo "⚠️  client_secret.json not found in data/ directory"
    echo "   Please download it from Google Cloud Console and place it in data/"
    echo "   Instructions: https://console.cloud.google.com/"
else
    echo "✅ client_secret.json found"
fi
echo ""

echo "🔨 Building Docker image..."
docker build -t youtube-migrator . || {
    echo "❌ Docker build failed"
    exit 1
}
echo "✅ Docker image built successfully"
echo ""

echo "🎉 Setup complete!"
echo ""
echo "To run the migrator:"
echo "  docker run -it --rm -v \$(pwd)/data:/app/data youtube-migrator"
echo ""
echo "Or with Docker Compose:"
echo "  docker-compose up"
echo ""
echo "For more information, see DOCKER.md"
