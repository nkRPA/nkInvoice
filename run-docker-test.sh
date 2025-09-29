#!/bin/bash

# Script to run nkInvoice tests in Docker
# Usage: ./run-docker-test.sh [headless|interactive]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting nkInvoice Docker Test Environment${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
    if [ -f "env.example" ]; then
        cp env.example .env
        echo -e "${YELLOW}📝 Please edit .env file with your actual credentials before running tests.${NC}"
        echo -e "${YELLOW}   You can edit it with: nano .env${NC}"
        exit 1
    else
        echo -e "${RED}❌ No env.example template found. Please create .env file manually.${NC}"
        exit 1
    fi
fi

# Create necessary directories
mkdir -p logs tmp

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Determine mode
MODE=${1:-interactive}

case $MODE in
    "headless")
        echo -e "${GREEN}🔧 Running in headless mode...${NC}"
        docker-compose up --build nkinvoice-headless
        ;;
    "interactive"|*)
        echo -e "${GREEN}🔧 Running in interactive mode...${NC}"
        docker-compose up --build nkinvoice-test
        ;;
esac

echo -e "${GREEN}✅ Test completed. Check logs/ directory for output files.${NC}"
