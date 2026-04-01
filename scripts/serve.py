"""
serve.py — Start lokal webserver og åpne modellen i nettleseren.

Dobbeltklikk på serve.bat, eller kjør:
    python serve.py

Modellen åpnes på http://localhost:8080
Live markedsdata (Yahoo Finance) fungerer fra http://, ikke fra file://
"""

import http.server
import socketserver
import threading
import webbrowser
import time
import os

PORT = 8080
DIR  = os.path.dirname(os.path.abspath(__file__))
URL  = f"http://localhost:{PORT}/index.html"

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)
    def log_message(self, format, *args):
        pass  # Ikke print hver forespørsel

def start_server():
    with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
        print(f"  Server kjører på {URL}")
        print(f"  Trykk Ctrl+C for å stoppe\n")
        httpd.serve_forever()

print("\n Geopolitisk Systemanalyse Investor 2026")
print("─" * 44)

# Start server i bakgrunnstråd
t = threading.Thread(target=start_server, daemon=True)
t.start()

# Vent litt, åpne nettleser
time.sleep(0.5)
webbrowser.open(URL)
print(f"  Åpner {URL} ...")

# Hold serveren i gang
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n  Server stoppet.")
