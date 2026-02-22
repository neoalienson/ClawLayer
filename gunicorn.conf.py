"""Gunicorn configuration for ClawLayer."""

bind = "0.0.0.0:11435"
workers = 4
worker_class = "gevent"  # Use gevent for SSE support
timeout = 120
keepalive = 5
worker_connections = 1000
