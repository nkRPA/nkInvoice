#!/bin/bash

# Script to install docker-compose on Ubuntu server
# Usage: ./install-docker-compose-ubuntu.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 Installing Docker Compose on Ubuntu Server${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  Running as root. This is fine for installation.${NC}"
fi

# Check if Docker is installed
if ! command -v docker > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo -e "${YELLOW}💡 Install Docker with:${NC}"
    echo -e "${YELLOW}   sudo apt update${NC}"
    echo -e "${YELLOW}   sudo apt install docker.io${NC}"
    echo -e "${YELLOW}   sudo systemctl start docker${NC}"
    echo -e "${YELLOW}   sudo systemctl enable docker${NC}"
    exit 1
fi

# Check if docker-compose is already installed
if command -v docker-compose > /dev/null 2>&1; then
    echo -e "${GREEN}✅ docker-compose is already installed.${NC}"
    docker-compose --version
    exit 0
fi

# Check if Docker Compose V2 is available
if docker compose version > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Compose V2 is available.${NC}"
    docker compose version
    echo -e "${YELLOW}💡 You can use 'docker compose' instead of 'docker-compose'${NC}"
    exit 0
fi

# Install docker-compose
echo -e "${GREEN}📦 Installing docker-compose...${NC}"

# Get the latest version
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')

# Download and install
sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Create symlink for easier access
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verify installation
if command -v docker-compose > /dev/null 2>&1; then
    echo -e "${GREEN}✅ docker-compose installed successfully!${NC}"
    docker-compose --version
else
    echo -e "${RED}❌ Installation failed.${NC}"
    exit 1
fi

# Add user to docker group (if not already)
if ! groups $USER | grep -q docker; then
    echo -e "${YELLOW}👤 Adding user to docker group...${NC}"
    sudo usermod -aG docker $USER
    echo -e "${YELLOW}⚠️  You need to logout and login again for group changes to take effect.${NC}"
    echo -e "${YELLOW}   Or run: newgrp docker${NC}"
fi

echo -e "${GREEN}🎉 Docker Compose installation complete!${NC}"
echo -e "${YELLOW}💡 Next steps:${NC}"
echo -e "${YELLOW}   1. Logout and login again (or run: newgrp docker)${NC}"
echo -e "${YELLOW}   2. Run: ./run-docker-ubuntu.sh headless${NC}"
