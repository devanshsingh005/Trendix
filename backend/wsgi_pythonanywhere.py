import os
import sys

# Add the project directory to the Python path
path = '/home/ayushthegreat/ProductAnalysis/backend'
if path not in sys.path:
    sys.path.insert(0, path)

# Set up Django's settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pullup.settings')

# Import and create the WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
