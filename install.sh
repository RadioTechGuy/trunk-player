#!/bin/bash
# Trunk Player Installation Script
# Automated setup for development environment

set -e  # Exit on any error

echo "=== Trunk Player Installation Script ==="
echo "This script will set up a development environment for Trunk Player"
echo ""

# Check if running from correct directory
if [ ! -f "manage.py" ] || [ ! -f "requirements.txt" ]; then
    echo "Error: This script must be run from the trunk-player directory"
    echo "Please run: cd trunk-player && ./install.sh"
    exit 1
fi

# Comprehensive prerequisite checks
echo "Checking system requirements..."

# Check Python version
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "Error: Python 3.8+ is required. Found: Python $PYTHON_VERSION"
    exit 1
fi
echo " Python $PYTHON_VERSION detected"

# Check for Homebrew on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew >/dev/null 2>&1; then
        echo "Installing Homebrew (required for macOS dependencies)..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add brew to PATH for this session
        if [[ -d "/opt/homebrew/bin" ]]; then
            export PATH="/opt/homebrew/bin:$PATH"
        elif [[ -d "/usr/local/bin" ]]; then
            export PATH="/usr/local/bin:$PATH"
        fi
        
        echo "Homebrew installed"
        echo ""
    else
        echo " Homebrew available"
    fi
fi

# Check for required system tools
MISSING_TOOLS=""
for tool in openssl sed; do
    if ! command -v $tool >/dev/null 2>&1; then
        MISSING_TOOLS="$MISSING_TOOLS $tool"
    fi
done

# Special check for pip (might be pip3)
if ! command -v pip >/dev/null 2>&1 && ! command -v pip3 >/dev/null 2>&1; then
    MISSING_TOOLS="$MISSING_TOOLS pip"
fi

if [ ! -z "$MISSING_TOOLS" ]; then
    echo "Error: Missing required tools:$MISSING_TOOLS"
    echo ""
    echo "Installation commands by platform:"
    echo ""
    
    if [[ $MISSING_TOOLS == *"pip"* ]]; then
        echo "For pip:"
        echo "  Ubuntu/Debian:  sudo apt update && sudo apt install python3-pip"
        echo "  RedHat/CentOS:  sudo yum install python3-pip"
        echo "  Fedora:         sudo dnf install python3-pip"
        echo "  macOS:          python3 -m ensurepip --upgrade"
        echo "  Alternative:    curl https://bootstrap.pypa.io/get-pip.py | python3"
        echo ""
    fi
    
    if [[ $MISSING_TOOLS == *"openssl"* ]]; then
        echo "For openssl:"
        echo "  Ubuntu/Debian:  sudo apt update && sudo apt install openssl"
        echo "  RedHat/CentOS:  sudo yum install openssl"
        echo "  Fedora:         sudo dnf install openssl"
        echo "  macOS:          brew install openssl"
        echo ""
    fi
    
    if [[ $MISSING_TOOLS == *"sed"* ]]; then
        echo "For sed:"
        echo "  Ubuntu/Debian:  sudo apt update && sudo apt install sed"
        echo "  RedHat/CentOS:  sudo yum install sed"
        echo "  Fedora:         sudo dnf install sed"
        echo "  macOS:          brew install gnu-sed"
        echo ""
    fi
    
    echo "Alternative: Use Docker deployment instead:"
    echo "  docker-compose up"
    echo ""
    
    echo "Installing missing tools automatically..."
        
        if [[ $MISSING_TOOLS == *"openssl"* ]]; then
            echo "Installing openssl..."
            if [[ "$OSTYPE" == "darwin"* ]]; then
                if command -v brew >/dev/null 2>&1; then
                    brew install openssl
                else
                    echo "ERROR: Homebrew not found. Please install Homebrew first:"
                    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                    exit 1
                fi
            else
                if command -v apt >/dev/null 2>&1; then
                    sudo apt update && sudo apt install -y openssl
                elif command -v dnf >/dev/null 2>&1; then
                    sudo dnf install -y openssl
                elif command -v yum >/dev/null 2>&1; then
                    sudo yum install -y openssl
                else
                    echo "ERROR: Could not determine package manager for openssl"
                    exit 1
                fi
            fi
            echo " openssl installed"
        fi
        
        if [[ $MISSING_TOOLS == *"sed"* ]]; then
            echo "Installing sed..."
            if [[ "$OSTYPE" == "darwin"* ]]; then
                if command -v brew >/dev/null 2>&1; then
                    brew install gnu-sed
                    # Note: gnu-sed installs as gsed, but we can alias it
                    echo "Note: GNU sed installed as 'gsed'. Creating alias..."
                    if ! grep -q "alias sed=gsed" ~/.bashrc 2>/dev/null && ! grep -q "alias sed=gsed" ~/.zshrc 2>/dev/null; then
                        echo "alias sed=gsed" >> ~/.bashrc 2>/dev/null || echo "alias sed=gsed" >> ~/.zshrc 2>/dev/null || true
                        echo "Added sed=gsed alias to shell profile"
                    fi
                else
                    echo "ERROR: Homebrew not found. Please install Homebrew first:"
                    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                    exit 1
                fi
            else
                if command -v apt >/dev/null 2>&1; then
                    sudo apt update && sudo apt install -y sed
                elif command -v dnf >/dev/null 2>&1; then
                    sudo dnf install -y sed
                elif command -v yum >/dev/null 2>&1; then
                    sudo yum install -y sed
                else
                    echo "ERROR: Could not determine package manager for sed"
                    exit 1
                fi
            fi
            echo " sed installed"
        fi
        
        if [[ $MISSING_TOOLS == *"pip"* ]]; then
            echo "Installing pip..."
            if [[ "$OSTYPE" == "darwin"* ]]; then
                python3 -m ensurepip --upgrade
                if [ $? -ne 0 ]; then
                    echo "Trying alternative pip installation..."
                    curl https://bootstrap.pypa.io/get-pip.py | python3
                fi
            else
                if command -v apt >/dev/null 2>&1; then
                    sudo apt update && sudo apt install -y python3-pip
                elif command -v dnf >/dev/null 2>&1; then
                    sudo dnf install -y python3-pip
                elif command -v yum >/dev/null 2>&1; then
                    sudo yum install -y python3-pip
                else
                    echo "ERROR: Could not determine package manager for pip"
                    exit 1
                fi
            fi
            echo " pip installed"
        fi
        
        echo " All missing tools installed successfully!"
        echo "Note: You may need to restart your terminal or source your shell profile"
        echo ""
fi

# Use pip3 if pip is not available but pip3 is
if ! command -v pip >/dev/null 2>&1 && command -v pip3 >/dev/null 2>&1; then
    echo "Using pip3 instead of pip"
    alias pip=pip3
fi

echo " Required system tools available"

# Check for venv module
if ! python3 -c "import venv" 2>/dev/null; then
    echo "Error: Python venv module not available"
    echo "On Ubuntu/Debian: sudo apt install python3-venv"
    echo "On RedHat/CentOS: sudo yum install python3-venv"
    exit 1
fi
echo " Python venv module available"

# Check disk space (need at least 500MB)
if command -v df >/dev/null 2>&1; then
    AVAILABLE_KB=$(df . | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE_KB" -lt 500000 ]; then
        echo "Warning: Low disk space detected ($(($AVAILABLE_KB/1024))MB available)"
        echo "Recommend at least 500MB free space"
    else
        echo " Sufficient disk space available"
    fi
fi

# Check internet connectivity for pip
if command -v curl >/dev/null 2>&1; then
    if ! curl -s --connect-timeout 5 https://pypi.org >/dev/null; then
        echo "Warning: Cannot connect to PyPI. Pip install may fail."
        echo "Consider using: pip install --find-links /path/to/local/wheels -r requirements.txt"
    else
        echo " Internet connectivity verified"
    fi
elif command -v wget >/dev/null 2>&1; then
    if ! wget -q --timeout=5 --spider https://pypi.org; then
        echo "Warning: Cannot connect to PyPI. Pip install may fail."
    else
        echo " Internet connectivity verified"
    fi
fi

# Check file permissions
if [ ! -w . ]; then
    echo "Error: No write permission in current directory"
    exit 1
fi
echo " Write permissions verified"

# Check for optional PostgreSQL
POSTGRES_AVAILABLE=false
if command -v psql >/dev/null 2>&1; then
    # Test if PostgreSQL is actually running and accessible
    if psql postgres -c '\q' >/dev/null 2>&1; then
        POSTGRES_AVAILABLE=true
        echo " PostgreSQL detected and accessible - database setup will be available"
    else
        echo "WARNING: PostgreSQL installed but not running or accessible"
        echo "  macOS: brew services start postgresql"
        echo "  Linux: sudo systemctl start postgresql"
        echo "  Will use SQLite for development"
    fi
else
    echo "WARNING: PostgreSQL not detected - will use SQLite for development"
    echo "  Install with: brew install postgresql (macOS)"
fi

# Check if already installed
CREATE_VENV=true
if [ -d "venv" ]; then
    echo "Warning: Virtual environment 'venv' already exists"
    
    # Check if the virtual environment has correct interpreter paths
    VENV_BROKEN=false
    if [ -f "venv/bin/python3" ]; then
        # Check if the python interpreter is accessible
        if ! venv/bin/python3 -c "import sys" >/dev/null 2>&1; then
            VENV_BROKEN=true
            echo "WARNING: Virtual environment appears to have broken interpreter paths"
        fi
    else
        VENV_BROKEN=true
        echo "WARNING: Virtual environment missing python interpreter"
    fi
    
    if [ "$VENV_BROKEN" = true ]; then
        echo "Virtual environment needs to be recreated due to path issues"
        echo "This commonly happens when the project directory is moved or copied"
        rm -rf venv
        echo "Removed broken virtual environment"
        CREATE_VENV=true
    else
        read -p "Remove and recreate virtual environment? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            echo "Removed existing virtual environment"
            CREATE_VENV=true
        else
            echo "Using existing virtual environment"
            CREATE_VENV=false
        fi
    fi
fi

echo "All prerequisite checks passed!"
echo ""

if [ "$CREATE_VENV" = true ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv --prompt='(Trunk Player)'
else
    echo "Using existing virtual environment..."
fi

source venv/bin/activate

echo "Upgrading pip and installing dependencies..."
pip install --upgrade pip

# Check if requirements need to be reinstalled
NEED_REINSTALL=false
if [ "$CREATE_VENV" = false ]; then
    echo "Checking installed packages..."
    # Test a few critical packages to see if they work
    if ! python -c "import django" >/dev/null 2>&1 || ! python -c "import channels" >/dev/null 2>&1; then
        echo "WARNING: Some packages appear to be missing or broken"
        echo "This can happen when the project directory is moved or copied"
        NEED_REINSTALL=true
    fi
fi

if [ "$NEED_REINSTALL" = true ]; then
    echo "Reinstalling all requirements to fix package paths..."
    pip install --force-reinstall -r requirements.txt
else
    pip install -r requirements.txt
fi

echo "Setting up local configuration..."
if [ ! -f "trunk_player/settings_local.py" ]; then
    if [ ! -f "trunk_player/settings_local.py.sample" ]; then
        echo "Error: settings_local.py.sample not found"
        exit 1
    fi
    cp trunk_player/settings_local.py.sample trunk_player/settings_local.py
    echo "Created trunk_player/settings_local.py from sample"
else
    echo "trunk_player/settings_local.py already exists, skipping..."
fi

echo "Generating secure Django secret key..."
djpass=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-64)

echo "Detecting network addresses..."

# Get primary IP address
if command -v ip >/dev/null 2>&1; then
    # Linux
    ip4=$(ip route get 8.8.8.8 2>/dev/null | sed -n '/src/{s/.*src *\([^ ]*\).*/\1/p;q}')
elif command -v route >/dev/null 2>&1; then
    # macOS/BSD
    ip4=$(route get 8.8.8.8 2>/dev/null | grep interface | awk '{print $2}' | xargs ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | head -1)
else
    # Fallback
    ip4=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
fi

# Get hostname
hostname_addr=$(hostname 2>/dev/null || echo "localhost")

# Get all local IP addresses (for comprehensive CSRF coverage)
all_ips=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - get all non-loopback IPv4 addresses
    all_ips=$(ifconfig | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | tr '\n' ' ')
else
    # Linux
    all_ips=$(hostname -I 2>/dev/null | tr '\n' ' ' || echo "")
fi

echo "Detected primary IP: $ip4"
echo "Detected hostname: $hostname_addr"
echo "All local IPs: $all_ips"

echo "Updating Django settings..."

# Build comprehensive allowed hosts list
allowed_hosts="'localhost', '127.0.0.1'"
csrf_origins="'http://localhost', 'http://127.0.0.1', 'https://localhost', 'https://127.0.0.1'"

# Add primary IP
if [ -n "$ip4" ] && [ "$ip4" != "localhost" ]; then
    allowed_hosts="$allowed_hosts, '$ip4'"
    csrf_origins="$csrf_origins, 'http://$ip4', 'https://$ip4'"
fi

# Add hostname if different from localhost
if [ -n "$hostname_addr" ] && [ "$hostname_addr" != "localhost" ] && [ "$hostname_addr" != "$ip4" ]; then
    allowed_hosts="$allowed_hosts, '$hostname_addr'"
    csrf_origins="$csrf_origins, 'http://$hostname_addr', 'https://$hostname_addr'"
fi

# Add all local IPs
for ip in $all_ips; do
    if [ "$ip" != "127.0.0.1" ] && [ "$ip" != "$ip4" ] && [ "$ip" != "$hostname_addr" ]; then
        allowed_hosts="$allowed_hosts, '$ip'"
        csrf_origins="$csrf_origins, 'http://$ip', 'https://$ip'"
    fi
done

echo "ALLOWED_HOSTS will include: $allowed_hosts"

# Cross-platform sed handling
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS requires backup extension
    sed -i '' "s/^SECRET_KEY = .*/SECRET_KEY = '$djpass'/" trunk_player/settings_local.py
    sed -i '' "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = [$allowed_hosts]/" trunk_player/settings_local.py
    sed -i '' "s|AUDIO_URL_BASE = '//s3.amazonaws.com/SET-TO-MY-BUCKET/'|AUDIO_URL_BASE = '/audio_files/'|" trunk_player/settings_local.py
    
    # Add CSRF_TRUSTED_ORIGINS after ALLOWED_HOSTS
    sed -i '' "/^ALLOWED_HOSTS = /a\\
\\
# CSRF trusted origins for Django 4.0+\\
CSRF_TRUSTED_ORIGINS = [\\
    $csrf_origins\\
]
" trunk_player/settings_local.py
else
    # Linux
    sed -i "s/^SECRET_KEY = .*/SECRET_KEY = '$djpass'/" trunk_player/settings_local.py
    sed -i "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = [$allowed_hosts]/" trunk_player/settings_local.py
    sed -i "s|AUDIO_URL_BASE = '//s3.amazonaws.com/SET-TO-MY-BUCKET/'|AUDIO_URL_BASE = '/audio_files/'|" trunk_player/settings_local.py
    
    # Add CSRF_TRUSTED_ORIGINS after ALLOWED_HOSTS
    sed -i "/^ALLOWED_HOSTS = /a\\
\\
# CSRF trusted origins for Django 4.0+\\
CSRF_TRUSTED_ORIGINS = [\\
    $csrf_origins\\
]" trunk_player/settings_local.py
fi

# Clean up sensitive variables
unset djpass

# Database setup
if [ "$POSTGRES_AVAILABLE" = true ]; then
    echo "Setting up PostgreSQL database..."
    
    # Generate secure database password
    dbpass=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-16)
    
    echo "Configuring database connection..."
    # Create SQL setup script inline
    cat > /tmp/postgres_setup_temp.sql << EOF
-- PostgreSQL Database Setup for Trunk Player
-- This script creates the database, user, and sets appropriate permissions

CREATE USER trunk_player_user WITH PASSWORD '$dbpass';
CREATE DATABASE trunk_player OWNER trunk_player_user;
GRANT ALL PRIVILEGES ON DATABASE trunk_player TO trunk_player_user;
ALTER ROLE trunk_player_user SET client_encoding TO 'utf8';
ALTER ROLE trunk_player_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE trunk_player_user SET timezone TO 'UTC';
\\c trunk_player
GRANT USAGE ON SCHEMA public TO trunk_player_user;
GRANT CREATE ON SCHEMA public TO trunk_player_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trunk_player_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trunk_player_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO trunk_player_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO trunk_player_user;
EOF
    
    # Update database settings
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/'PASSWORD': 'fake_password',/'PASSWORD': '$dbpass',/" trunk_player/settings_local.py
    else
        sed -i "s/'PASSWORD': 'fake_password',/'PASSWORD': '$dbpass',/" trunk_player/settings_local.py
    fi
    
    # Check if database/user already exists
    echo "Checking for existing database setup..."
    
    DB_EXISTS=false
    USER_EXISTS=false
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - check as current user
        if command -v createdb >/dev/null 2>&1; then
            # Check if database exists
            if psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='trunk_player';" 2>/dev/null | grep -q 1; then
                DB_EXISTS=true
                echo "WARNING: Database 'trunk_player' already exists"
            fi
            # Check if user exists
            if psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='trunk_player_user';" 2>/dev/null | grep -q 1; then
                USER_EXISTS=true
                echo "WARNING: User 'trunk_player_user' already exists"
            fi
        else
            echo "Error: PostgreSQL command-line tools not found"
            echo "Install with: brew install postgresql"
            echo "Or use Docker deployment instead"
            rm -f /tmp/postgres_setup_temp.sql
            exit 1
        fi
    else
        # Linux - check with appropriate user
        if id -u postgres >/dev/null 2>&1; then
            # Check if database exists
            if sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='trunk_player';" 2>/dev/null | grep -q 1; then
                DB_EXISTS=true
                echo "WARNING: Database 'trunk_player' already exists"
            fi
            # Check if user exists
            if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='trunk_player_user';" 2>/dev/null | grep -q 1; then
                USER_EXISTS=true
                echo "WARNING: User 'trunk_player_user' already exists"
            fi
        else
            echo "PostgreSQL postgres user not found"
            echo "Try running manually or install PostgreSQL properly"
            rm -f /tmp/postgres_setup_temp.sql
            exit 1
        fi
    fi
    
    # Handle existing database/user
    if [ "$DB_EXISTS" = true ] || [ "$USER_EXISTS" = true ]; then
        echo ""
        echo "Existing PostgreSQL setup detected:"
        [ "$DB_EXISTS" = true ] && echo "  - Database 'trunk_player' exists"
        [ "$USER_EXISTS" = true ] && echo "  - User 'trunk_player_user' exists"
        echo ""
        echo "Options:"
        echo "1. Drop and recreate (DESTROYS ALL DATA)"
        echo "2. Use existing setup (recommended)"
        echo "3. Skip database setup"
        echo ""
        read -p "Choose option (1/2/3): " -n 1 -r
        echo
        
        case $REPLY in
            1)
                echo "Dropping existing database and user..."
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    [ "$DB_EXISTS" = true ] && psql postgres -c "DROP DATABASE IF EXISTS trunk_player;" 2>/dev/null
                    [ "$USER_EXISTS" = true ] && psql postgres -c "DROP USER IF EXISTS trunk_player_user;" 2>/dev/null
                else
                    [ "$DB_EXISTS" = true ] && sudo -u postgres psql -c "DROP DATABASE IF EXISTS trunk_player;" 2>/dev/null
                    [ "$USER_EXISTS" = true ] && sudo -u postgres psql -c "DROP USER IF EXISTS trunk_player_user;" 2>/dev/null
                fi
                echo " Existing setup removed"
                
                # Proceed with setup
                echo "Creating fresh database setup..."
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    psql postgres < /tmp/postgres_setup_temp.sql
                else
                    sudo -u postgres psql < /tmp/postgres_setup_temp.sql
                fi
                ;;
            2)
                echo "Using existing database setup"
                echo "Note: Make sure the password in settings_local.py matches the existing user"
                ;;
            3)
                echo "Skipping database setup"
                rm -f /tmp/postgres_setup_temp.sql
                unset dbpass
                echo "WARNING: You'll need to configure the database manually"
                ;;
            *)
                echo "Invalid option. Using existing setup."
                ;;
        esac
    else
        # No existing setup, proceed normally
        echo "Creating new database setup..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            psql postgres < /tmp/postgres_setup_temp.sql
        else
            sudo -u postgres psql < /tmp/postgres_setup_temp.sql
        fi
    fi
    
    rm -f /tmp/postgres_setup_temp.sql
    
    # Clean up sensitive variables
    unset dbpass
    
    echo "PostgreSQL database setup complete!"
else
    echo "PostgreSQL not available - using SQLite for development"
    echo "For production, install PostgreSQL and re-run this installer"
fi

echo "Running Django database migrations..."
python manage.py migrate

echo "Creating directories..."
mkdir -p audio_files
mkdir -p logs
mkdir -p static

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "Creating superuser account..."
echo "You'll need this to access the Django admin interface."
python manage.py createsuperuser

echo ""
echo "=== Installation Complete! ==="
echo ""

# Automatic production setup
echo ""
echo "=== Production Setup ==="
echo "Configuring web server, process management, and logging..."
echo ""

# Check for production services
echo "Checking for production services..."

# Check Nginx
NGINX_INSTALLED=false
NGINX_RUNNING=false

if command -v nginx >/dev/null 2>&1; then
    NGINX_INSTALLED=true
    echo " Nginx installed"
    
    # Check if nginx is running
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if brew services list | grep nginx | grep started >/dev/null 2>&1; then
            NGINX_RUNNING=true
            echo " Nginx running"
        else
            echo "WARNING: Nginx installed but not running"
        fi
    else
        if systemctl is-active --quiet nginx; then
            NGINX_RUNNING=true
            echo " Nginx running"
        else
            echo "WARNING: Nginx installed but not running"
        fi
    fi
else
    echo "ERROR: Nginx not installed"
fi
    
    # Check Supervisor
    SUPERVISOR_INSTALLED=false
    SUPERVISOR_RUNNING=false
    
    if command -v supervisorctl >/dev/null 2>&1; then
        SUPERVISOR_INSTALLED=true
        echo " Supervisor installed"
        
        # Check if supervisor is running
        if supervisorctl status >/dev/null 2>&1; then
            SUPERVISOR_RUNNING=true
            echo " Supervisor running"
        else
            echo "WARNING: Supervisor installed but not running"
        fi
    else
        echo "ERROR: Supervisor not installed"
    fi
    
    # Handle missing services
    if [ "$NGINX_INSTALLED" = false ] || [ "$SUPERVISOR_INSTALLED" = false ]; then
        echo ""
        echo "Missing required services. Installation commands:"
        echo ""
        
        if [ "$NGINX_INSTALLED" = false ]; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                echo "Install Nginx:     brew install nginx"
            else
                echo "Install Nginx:     sudo apt install nginx  # Ubuntu/Debian"
                echo "                   sudo yum install nginx  # RHEL/CentOS"
                echo "                   sudo dnf install nginx  # Fedora"
            fi
        fi
        
        if [ "$SUPERVISOR_INSTALLED" = false ]; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                echo "Install Supervisor: brew install supervisor"
            else
                echo "Install Supervisor: sudo apt install supervisor  # Ubuntu/Debian"
                echo "                    sudo yum install supervisor  # RHEL/CentOS"
                echo "                    sudo dnf install supervisor  # Fedora"
            fi
        fi
        
        echo ""
        echo "Installing missing services automatically..."
            
            if [ "$NGINX_INSTALLED" = false ]; then
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    brew install nginx
                else
                    if command -v apt >/dev/null 2>&1; then
                        sudo apt update && sudo apt install -y nginx
                    elif command -v dnf >/dev/null 2>&1; then
                        sudo dnf install -y nginx
                    elif command -v yum >/dev/null 2>&1; then
                        sudo yum install -y nginx
                    else
                        echo "ERROR: Could not determine package manager. Please install nginx manually."
                        exit 1
                    fi
                fi
                echo " Nginx installed"
            fi
            
            if [ "$SUPERVISOR_INSTALLED" = false ]; then
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    brew install supervisor
                else
                    if command -v apt >/dev/null 2>&1; then
                        sudo apt install -y supervisor
                    elif command -v dnf >/dev/null 2>&1; then
                        sudo dnf install -y supervisor
                    elif command -v yum >/dev/null 2>&1; then
                        sudo yum install -y supervisor
                    else
                        echo "ERROR: Could not determine package manager. Please install supervisor manually."
                        exit 1
                    fi
                fi
                echo " Supervisor installed"
            fi
    fi
    
    # Start services if not running
    if [ "$NGINX_RUNNING" = false ]; then
        echo "Starting Nginx..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start nginx
        else
            sudo systemctl start nginx
            sudo systemctl enable nginx
        fi
    fi
    
    if [ "$SUPERVISOR_RUNNING" = false ]; then
        echo "Starting Supervisor..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start supervisor
        else
            sudo systemctl start supervisor
            sudo systemctl enable supervisor
        fi
    fi
    
    echo " All required services are installed and running"
    echo ""
    
    # Create production log directory
    echo "Creating production log directory..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - use Homebrew prefix var/log
        HOMEBREW_PREFIX=$(brew --prefix)
        PROD_LOG_DIR="$HOMEBREW_PREFIX/var/log/trunk-player"
        mkdir -p $PROD_LOG_DIR
    else
        # Linux
        PROD_LOG_DIR="/var/log/trunk-player"
        sudo mkdir -p $PROD_LOG_DIR
        sudo chown $USER:$USER $PROD_LOG_DIR
    fi
    echo " Production log directory created: $PROD_LOG_DIR"
    
    # Setup Nginx configuration
    echo "Setting up Nginx configuration..."
    if [ ! -f "trunk_player/trunk_player.nginx.sample" ]; then
        echo "Error: trunk_player.nginx.sample not found"
        exit 1
    fi
    
    # Copy and customize nginx config
    cp trunk_player/trunk_player.nginx.sample trunk_player/trunk_player.nginx
    
    # Update paths in nginx config for current installation
    INSTALL_DIR=$(pwd)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|/home/radio/trunk-player|$INSTALL_DIR|g" trunk_player/trunk_player.nginx
        sed -i '' "s|/var/log/trunk-player|$PROD_LOG_DIR|g" trunk_player/trunk_player.nginx
    else
        sed -i "s|/home/radio/trunk-player|$INSTALL_DIR|g" trunk_player/trunk_player.nginx
        sed -i "s|/var/log/trunk-player|$PROD_LOG_DIR|g" trunk_player/trunk_player.nginx
    fi
    
    # Install nginx config
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS with Homebrew nginx - detect correct homebrew prefix
        HOMEBREW_PREFIX=$(brew --prefix)
        NGINX_CONFIG_DIR="$HOMEBREW_PREFIX/etc/nginx/servers"
        NGINX_MAIN_CONF="$HOMEBREW_PREFIX/etc/nginx/nginx.conf"
        
        # Create nginx servers directory if it doesn't exist
        if [ ! -d "$NGINX_CONFIG_DIR" ]; then
            echo "Creating nginx servers directory: $NGINX_CONFIG_DIR"
            mkdir -p "$NGINX_CONFIG_DIR"
        fi
        
        # Create symlink to our config
        ln -sf $INSTALL_DIR/trunk_player/trunk_player.nginx $NGINX_CONFIG_DIR/trunk_player.conf
        echo " Nginx site configuration linked"
        
        # Check if main nginx.conf includes servers directory
        if [ -f "$NGINX_MAIN_CONF" ] && ! grep -q "include.*servers/\*" "$NGINX_MAIN_CONF" 2>/dev/null; then
            echo "Updating nginx.conf to include servers directory..."
            # Backup original
            cp "$NGINX_MAIN_CONF" "$NGINX_MAIN_CONF.backup.$(date +%Y%m%d_%H%M%S)"
            
            # Add include directive in http block
            sed -i '' '/^[[:space:]]*include[[:space:]]*mime.types;/a\
    include '"$HOMEBREW_PREFIX"'/etc/nginx/servers/*;
' "$NGINX_MAIN_CONF"
            echo " Updated nginx.conf to include server configs"
        fi
        
        # Test nginx configuration
        echo "Testing nginx configuration..."
        if nginx -t; then
            echo " Nginx configuration valid"
        else
            echo "ERROR: Nginx configuration test failed"
            echo "Please check the configuration manually"
        fi
        
        # Restart nginx
        echo "Restarting Nginx..."
        brew services restart nginx
    else
        # Linux
        sudo ln -sf $INSTALL_DIR/trunk_player/trunk_player.nginx /etc/nginx/sites-enabled/trunk_player
        sudo rm -f /etc/nginx/sites-enabled/default
        
        # Test and restart nginx
        sudo nginx -t
        sudo systemctl restart nginx
    fi
    echo " Nginx configured"
    
    # Setup process management
    echo "Setting up process management..."
    if [ ! -f "trunk_player/supervisor.conf.sample" ]; then
        echo "Error: supervisor.conf.sample not found"
        exit 1
    fi
    
    # Copy and customize supervisor config
    cp trunk_player/supervisor.conf.sample trunk_player/supervisor.conf
    
    # Update paths and user in supervisor config
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|/home/radio/trunk-player|$INSTALL_DIR|g" trunk_player/supervisor.conf
        sed -i '' "s|user=radio|user=$USER|g" trunk_player/supervisor.conf
        # Handle both env and venv directory names
        sed -i '' "s|/home/radio/trunk-player/env|$INSTALL_DIR/venv|g" trunk_player/supervisor.conf
        sed -i '' "s|trunk-player/env|trunk-player-mods/venv|g" trunk_player/supervisor.conf
        sed -i '' "s|/var/log/trunk-player|$PROD_LOG_DIR|g" trunk_player/supervisor.conf
    else
        sed -i "s|/home/radio/trunk-player|$INSTALL_DIR|g" trunk_player/supervisor.conf
        sed -i "s|user=radio|user=$USER|g" trunk_player/supervisor.conf
        # Handle both env and venv directory names
        sed -i "s|/home/radio/trunk-player/env|$INSTALL_DIR/venv|g" trunk_player/supervisor.conf
        sed -i "s|trunk-player/env|trunk-player-mods/venv|g" trunk_player/supervisor.conf
        sed -i "s|/var/log/trunk-player|$PROD_LOG_DIR|g" trunk_player/supervisor.conf
    fi
    
    # Create logs directory for supervisor
    mkdir -p $INSTALL_DIR/logs
    
    # Install supervisor config
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        SUPERVISOR_CONFIG_DIR="$HOMEBREW_PREFIX/etc/supervisor.d"
        mkdir -p $SUPERVISOR_CONFIG_DIR 2>/dev/null || true
        ln -sf $INSTALL_DIR/trunk_player/supervisor.conf $SUPERVISOR_CONFIG_DIR/trunk_player.conf
        
        # Create .ini symlink (supervisor looks for .ini files)
        ln -sf $SUPERVISOR_CONFIG_DIR/trunk_player.conf $SUPERVISOR_CONFIG_DIR/trunk_player.ini
        
        # Restart supervisor with error handling
        echo "Restarting supervisor..."
        brew services restart supervisor
        
        # Wait for supervisor to fully start
        sleep 2
        
        # Update supervisor processes with retry logic
        echo "Updating supervisor configuration..."
        for i in {1..3}; do
            if supervisorctl reread && supervisorctl update; then
                echo "Supervisor configuration updated successfully"
                break
            else
                echo "Supervisor update attempt $i failed, retrying in 2 seconds..."
                sleep 2
            fi
        done
    else
        # Linux
        sudo ln -sf $INSTALL_DIR/trunk_player/supervisor.conf /etc/supervisor/conf.d/trunk_player.conf
        sudo supervisorctl reread
        sudo supervisorctl update
    fi
    echo " Supervisor configured"
    
    # Setup trunk-recorder integration (if applicable)
    if [ -d "utility/trunk-recoder" ] && [ -f "utility/trunk-recoder/encode-local-sys-0.sh" ]; then
        echo "Setting up trunk-recorder integration..."
        
        # Look for common trunk-recorder locations
        TRUNK_RECORDER_DIRS=(
            "/home/$USER/trunk-recorder-build"
            "/usr/local/trunk-recorder"
            "/opt/trunk-recorder"
            "$HOME/trunk-recorder"
        )
        
        TRUNK_RECORDER_DIR=""
        for dir in "${TRUNK_RECORDER_DIRS[@]}"; do
            if [ -d "$dir" ]; then
                TRUNK_RECORDER_DIR="$dir"
                break
            fi
        done
        
        if [ -n "$TRUNK_RECORDER_DIR" ]; then
            cp utility/trunk-recoder/encode-local-sys-0.sh $TRUNK_RECORDER_DIR/
            chmod +x $TRUNK_RECORDER_DIR/encode-local-sys-0.sh
            echo " Trunk-recorder integration configured: $TRUNK_RECORDER_DIR"
        else
            echo "WARNING: Trunk-recorder directory not found. Copy manually if needed:"
            echo "  cp utility/trunk-recoder/encode-local-sys-0.sh /path/to/trunk-recorder/"
        fi
    fi
    
    # Start services
    echo ""
    echo "Starting services..."
    if command -v supervisorctl >/dev/null 2>&1; then
        supervisorctl start trunkplayer: 2>/dev/null || echo "Note: Start services with: supervisorctl start trunkplayer:"
    fi
    
    echo "Production setup complete!"

echo ""
echo "=== Installation Complete! ==="