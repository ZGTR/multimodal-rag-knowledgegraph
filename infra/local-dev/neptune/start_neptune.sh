#!/bin/bash

# Start Neptune (JanusGraph) locally for development
echo "🚀 Starting Neptune (JanusGraph) locally..."
echo "=========================================="

# Navigate to the Neptune directory
cd "$(dirname "$0")"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping any existing Neptune containers..."
docker-compose down

# Start Neptune
echo "🏗️  Starting Neptune with Docker Compose..."
docker-compose up -d

# Wait for Neptune to be ready
echo "⏳ Waiting for Neptune to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8182/status > /dev/null 2>&1; then
        echo "✅ Neptune is ready!"
        echo ""
        echo "📊 Neptune Status:"
        echo "   Endpoint: ws://localhost:8182/gremlin"
        echo "   HTTP Status: http://localhost:8182/status"
        echo "   Container: janusgraph-local"
        echo ""
        echo "🔗 Useful commands:"
        echo "   View logs: docker-compose logs -f"
        echo "   Stop Neptune: docker-compose down"
        echo "   Restart Neptune: docker-compose restart"
        echo ""
        echo "🎯 Next steps:"
        echo "   1. Start your API server: uvicorn src.api.main:app --reload"
        echo "   2. Test the connection with your ingest requests"
        exit 0
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

echo "❌ Neptune failed to start within 60 seconds"
echo "Check the logs with: docker-compose logs"
exit 1 