#!/bin/bash
cat > .env << 'EOF'
ADMIN_USERNAME=xiaomao
ADMIN_PASSWORD=45004879te
SECRET_KEY=minecraft_autologin_secret_key_2026_production
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=minecraft_autologin
ENCRYPTION_KEY=79zsyoRbeZ_bc8U25C8pb7i72H5KwSWTTPNZDatW_a4=
EOF
echo ".env created"
