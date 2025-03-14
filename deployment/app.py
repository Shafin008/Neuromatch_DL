# Imports
import io
import platform
from PIL import Image
from urllib.request import urlopen

import flasgger
from flask_restful import Api
from flask_restful import Resource, fields, marshal
from flask import Flask, render_template_string, request, redirect
# from flask_ngrok import run_with_ngrok 

import torch
from torchvision import models
import torchvision.transforms as transforms

import time
import json
import atexit
import requests
import subprocess
from threading import Timer
from flask import Flask

def _run_ngrok(port):
    """Starts ngrok and retrieves the public URL."""
    ngrok = subprocess.Popen(["ngrok", "http", str(port), "--region=ap"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    atexit.register(ngrok.terminate)  # Ensure ngrok stops when script ends

    localhost_url = "http://localhost:4040/api/tunnels"  # URL with tunnel details
    time.sleep(2)  # Give ngrok some time to start

    for _ in range(5):  # Retry up to 5 times if tunnels aren't available immediately
        try:
            tunnel_info = requests.get(localhost_url).json()
            tunnels = tunnel_info.get("tunnels", [])
            if tunnels:  # Ensure tunnels list is not empty
                return tunnels[0]["public_url"]  # Get the public ngrok URL
        except requests.exceptions.RequestException:
            time.sleep(1)  # Wait and retry

    raise RuntimeError("Failed to start ngrok. Please check if ngrok is installed and running.")

def start_ngrok(port):
    """Starts ngrok and prints the public URL."""
    try:
        ngrok_address = _run_ngrok(port)
        print(f" * Running on {ngrok_address}")
        print(" * Traffic stats available on http://127.0.0.1:4040")
    except RuntimeError as e:
        print(f"Error: {e}")

def run_with_ngrok(app):
    """
    The provided Flask app will be securely exposed to the public internet via ngrok.
    """
    old_run = app.run

    def new_run(*args, **kwargs):
        port = kwargs.get("port", 5000)  # Default port 5000
        thread = Timer(1, start_ngrok, args=(port,))
        thread.daemon = True  # Replaces deprecated setDaemon(True)
        thread.start()
        old_run(*args, **kwargs)

    app.run = new_run

# Create Flask app
app = Flask(__name__)

@app.route("/")
def home():
    """Root URL handler."""
    return "<h1>Welcome to Neuromatch</h1>"

# Run the Flask app with ngrok
run_with_ngrok(app)

# Start the app
app.run()