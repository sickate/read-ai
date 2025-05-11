#!/bin/bash

# Exit on error
set -e

# Variables
DOMAIN="instap.net"  # Replace with your domain
APP_NAME="read-ai"
APP_DIR="/var/www/$APP_NAME"
USER="tzhu"  # Default user on Aliyun Ubuntu instances

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Create a Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv $APP_DIR/venv
source $APP_DIR/venv/bin/activate

# Install Flask and Gunicorn (assuming your app requirements are in requirements.txt)
echo "Installing Flask and Gunicorn..."
pip install wheel
pip install gunicorn flask


# Create a Gunicorn systemd service
echo "Creating Gunicorn systemd service..."
sudo bash -c "cat > /etc/systemd/system/$APP_NAME.service" << EOF
[Unit]
Description=Gunicorn instance to serve $APP_NAME
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind unix:$APP_DIR/$APP_NAME.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
EOF

# Start and enable the Gunicorn service
echo "Starting Gunicorn service..."
sudo systemctl start $APP_NAME
sudo systemctl enable $APP_NAME

# Create Nginx configuration
echo "Configuring Nginx..."
sudo bash -c "cat > /etc/nginx/sites-available/$APP_NAME" << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/$APP_NAME.sock;
    }
}
EOF

# Enable the Nginx configuration
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Restart Nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx

# Configure firewall to allow web traffic
echo "Configuring firewall..."
sudo apt install -y ufw
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

# Set up SSL with Certbot
echo "Setting up SSL with Certbot..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Create a script to renew the certificate
echo "Creating SSL renewal cron job..."
echo "0 3 * * * root certbot renew --quiet" | sudo tee -a /etc/crontab > /dev/null

echo "======================================================"
echo "Setup completed!"
echo "Your Flask application is now running with Nginx and SSL"
echo "Please modify the domain name in this script and the Flask application as needed"
echo "Don't forget to set up proper DNS records for your domain"
echo "======================================================"
