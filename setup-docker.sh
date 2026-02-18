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

# Check for client_secret.json — prompt to paste if missing
if [ ! -f "data/client_secret.json" ]; then
    echo "⚠️  client_secret.json not found in data/ directory"
    echo ""
    echo "You can either:"
    echo "  A) Place it manually at data/client_secret.json, then re-run this script"
    echo "  B) Paste the JSON content now"
    echo ""
    read -p "Paste now? (y/n): " PASTE_NOW
    if [[ "$PASTE_NOW" == "y" || "$PASTE_NOW" == "Y" ]]; then
        echo "Paste your client_secret.json content below."
        echo "When done, type END on a new line and press Enter:"
        LINES=()
        while IFS= read -r line; do
            [[ "$line" == "END" ]] && break
            LINES+=("$line")
        done
        printf '%s\n' "${LINES[@]}" > data/client_secret.json
        echo "✅ client_secret.json saved to data/"
    else
        echo "⚠️  Skipping. Place client_secret.json in data/ before running the container."
    fi
else
    echo "✅ client_secret.json found"
fi

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
