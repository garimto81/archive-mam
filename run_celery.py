#!/usr/bin/env python
"""
Run Celery worker
"""
import subprocess
import sys

if __name__ == "__main__":
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "src.celery_app:celery_app",
        "worker",
        "--loglevel=info"
    ]
    subprocess.run(cmd)