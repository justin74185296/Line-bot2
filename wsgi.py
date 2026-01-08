"""
WSGI 入口點 - 用於 Gunicorn
"""
from main import app

if __name__ == "__main__":
    app.run()
