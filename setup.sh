#!/bin/bash

# Sahool Platform - Quick Setup Script
# This script helps you quickly set up and run different components of the Sahool platform

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║              🌾 Sahool Platform Setup 🌾                  ║"
    echo "║                                                            ║"
    echo "║         Smart Agricultural Management Platform            ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

# Main menu
show_menu() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}What would you like to set up?${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  1) 🐳 Full Platform (Docker Compose)"
    echo "  2) 📱 Mobile App (React Native)"
    echo "  3) 🌐 IoT Gateway Service"
    echo "  4) 🔗 Blockchain Supply Chain"
    echo "  5) ⚛️  Frontend (Next.js)"
    echo "  6) 🔧 Check Prerequisites"
    echo "  7) 📚 View Documentation"
    echo "  8) 🚀 Quick Start (All Services)"
    echo "  9) ❌ Exit"
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -n "Enter your choice [1-9]: "
}

check_prerequisites() {
    print_info "Checking prerequisites..."
    echo ""
    
    local all_ok=true
    
    # Check Docker
    if check_command docker; then
        docker --version
    else
        all_ok=false
        print_warning "Install Docker: https://docs.docker.com/get-docker/"
    fi
    
    # Check Docker Compose
    if check_command docker-compose; then
        docker-compose --version
    else
        all_ok=false
        print_warning "Install Docker Compose: https://docs.docker.com/compose/install/"
    fi
    
    # Check Node.js
    if check_command node; then
        node --version
    else
        all_ok=false
        print_warning "Install Node.js: https://nodejs.org/"
    fi
    
    # Check npm
    if check_command npm; then
        npm --version
    else
        all_ok=false
    fi
    
    # Check Python
    if check_command python3; then
        python3 --version
    else
        all_ok=false
        print_warning "Install Python 3: https://www.python.org/downloads/"
    fi
    
    # Check Git
    if check_command git; then
        git --version
    else
        all_ok=false
        print_warning "Install Git: https://git-scm.com/downloads/"
    fi
    
    echo ""
    if [ "$all_ok" = true ]; then
        print_success "All prerequisites are installed! ✨"
    else
        print_warning "Some prerequisites are missing. Please install them first."
    fi
}

setup_docker_platform() {
    print_info "Setting up Full Platform with Docker Compose..."
    echo ""
    
    if [ ! -f "docker-compose.enterprise.yml" ]; then
        print_error "docker-compose.enterprise.yml not found!"
        return 1
    fi
    
    print_info "Starting all services..."
    docker-compose -f docker-compose.enterprise.yml up -d
    
    print_success "Platform is starting up!"
    echo ""
    print_info "Services will be available at:"
    echo "  - Gateway: http://localhost:8000"
    echo "  - Platform Core: http://localhost:8001"
    echo "  - Frontend: http://localhost:3000"
    echo ""
    print_info "View logs: docker-compose -f docker-compose.enterprise.yml logs -f"
}

setup_mobile_app() {
    print_info "Setting up Mobile App..."
    echo ""
    
    cd mobile-app
    
    if [ ! -f "package.json" ]; then
        print_error "package.json not found in mobile-app directory!"
        return 1
    fi
    
    print_info "Installing dependencies..."
    npm install
    
    print_success "Mobile app is ready!"
    echo ""
    print_info "To start the app:"
    echo "  cd mobile-app"
    echo "  npm start"
    echo ""
    print_info "Then scan the QR code with Expo Go app on your phone"
    
    cd ..
}

setup_iot_gateway() {
    print_info "Setting up IoT Gateway Service..."
    echo ""
    
    cd iot-gateway
    
    if [ ! -f "requirements.txt" ]; then
        print_warning "requirements.txt not found, creating one..."
        cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
paho-mqtt==1.6.1
python-dotenv==1.0.0
httpx==0.25.0
EOF
    fi
    
    print_info "Creating virtual environment..."
    python3 -m venv venv
    
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    print_info "Installing dependencies..."
    pip install -r requirements.txt
    
    print_success "IoT Gateway is ready!"
    echo ""
    print_info "To start the service:"
    echo "  cd iot-gateway"
    echo "  source venv/bin/activate"
    echo "  uvicorn app.main:app --reload --port 8005"
    
    cd ..
}

setup_blockchain() {
    print_info "Setting up Blockchain Supply Chain..."
    echo ""
    
    cd blockchain-supply-chain
    
    if [ ! -f "package.json" ]; then
        print_error "package.json not found in blockchain-supply-chain directory!"
        return 1
    fi
    
    print_info "Installing dependencies..."
    npm install
    
    print_info "Compiling smart contracts..."
    npm run compile
    
    print_success "Blockchain is ready!"
    echo ""
    print_info "To deploy contracts:"
    echo "  cd blockchain-supply-chain"
    echo "  npm run deploy:testnet  # For Mumbai testnet"
    echo "  npm run deploy:mainnet  # For Polygon mainnet"
    
    cd ..
}

setup_frontend() {
    print_info "Setting up Frontend (Next.js)..."
    echo ""
    
    cd web
    
    if [ ! -f "package.json" ]; then
        print_error "package.json not found in web directory!"
        return 1
    fi
    
    print_info "Installing dependencies..."
    npm install
    
    print_success "Frontend is ready!"
    echo ""
    print_info "To start the frontend:"
    echo "  cd web"
    echo "  npm run dev"
    echo ""
    print_info "Then open http://localhost:3000 in your browser"
    
    cd ..
}

quick_start() {
    print_info "Quick Start - Setting up all services..."
    echo ""
    
    print_info "This will set up:"
    echo "  ✓ Docker Platform"
    echo "  ✓ Mobile App"
    echo "  ✓ IoT Gateway"
    echo "  ✓ Blockchain"
    echo "  ✓ Frontend"
    echo ""
    
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    setup_docker_platform
    setup_mobile_app
    setup_iot_gateway
    setup_blockchain
    setup_frontend
    
    print_success "All services are set up! 🎉"
    echo ""
    print_info "Next steps:"
    echo "  1. Configure environment variables (.env files)"
    echo "  2. Start the services you need"
    echo "  3. Check the documentation for each component"
}

view_documentation() {
    echo ""
    print_info "📚 Documentation Links:"
    echo ""
    echo "  📱 Mobile App:          mobile-app/README.md"
    echo "  🌐 IoT Gateway:         iot-gateway/README.md"
    echo "  🔗 Blockchain:          blockchain-supply-chain/README.md"
    echo "  ⚛️  Frontend:            web/README.md"
    echo "  📊 Gap Analysis:        GAP_ANALYSIS_REPORT.md"
    echo "  🏗️  Architecture:        ARCHITECTURE.md"
    echo "  🔧 Development:         DEVELOPMENT.md"
    echo ""
    print_info "Online Documentation:"
    echo "  🌐 GitHub: https://github.com/kafaat/sahool-project"
    echo ""
}

# Main script
main() {
    print_header
    
    while true; do
        show_menu
        read choice
        
        case $choice in
            1)
                setup_docker_platform
                ;;
            2)
                setup_mobile_app
                ;;
            3)
                setup_iot_gateway
                ;;
            4)
                setup_blockchain
                ;;
            5)
                setup_frontend
                ;;
            6)
                check_prerequisites
                ;;
            7)
                view_documentation
                ;;
            8)
                quick_start
                ;;
            9)
                print_info "Goodbye! 👋"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please choose 1-9."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function
main
