# Playlist
insert cool logo and description here

# Table of Contents
1. [Setup](#setup)

## Setup
Install redis: https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/install-redis-on-linux/


To start processes locally:
```
# Create virtual environment.
python -m venv venv

# Activate virtual environment.
activate_venv.bat

# Install dependencies.
pip install -r requirements.txt

# Start redis cache. Needed for websocket server.
service redis-server start

# Start http server.
python -m http_server.server

# Start websocket server.
python -m ws_server.server

# Run python sample client.
python clients\client.py --band "Band Name"
```