# gunicorn_config.py
"""
Gunicorn configuration for production deployment
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Threading
threads = 2

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Process naming
proc_name = "farmconnect"

# Server mechanics
daemon = False
pidfile = "logs/farmconnect.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if using HTTPS)
# keyfile = "certs/private.key"
# certfile = "certs/certificate.crt"

# Environment variables
raw_env = [
    "FLASK_APP=app.py",
    "FLASK_ENV=production"
]

def post_fork(server, worker):
    """Post fork hook"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """Pre fork hook"""
    pass

def pre_exec(server):
    """Pre exec hook"""
    server.log.info("Forked child, re-executing")

def when_ready(server):
    """When server is ready"""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Worker interrupt"""
    worker.log.info("Worker interrupted")

def worker_abort(worker):
    """Worker abort"""
    worker.log.info("Worker aborted")