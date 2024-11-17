import os
import sys
import logging

# Configure logging to use sys.stderr
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Log the current Python path
logging.debug('Current Python path: %s', sys.path)

try:
    # Add the project directory to the Python path
    path = '/home/ayushthegreat/ProductAnalysis/backend'
    if path not in sys.path:
        sys.path.insert(0, path)
        logging.debug('Added %s to Python path', path)

    # Add the parent directory to Python path as well
    parent_path = os.path.dirname(path)
    if parent_path not in sys.path:
        sys.path.insert(0, parent_path)
        logging.debug('Added %s to Python path', parent_path)

    # Set up Django's settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pullup.settings')
    logging.debug('Set DJANGO_SETTINGS_MODULE to %s', os.environ['DJANGO_SETTINGS_MODULE'])

    # Try importing Django settings to verify they can be loaded
    try:
        from pullup import settings
        logging.debug('Successfully imported Django settings')
    except Exception as e:
        logging.error('Failed to import Django settings: %s', str(e))
        raise

    # Import and create the WSGI application
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    logging.debug('Successfully created WSGI application')

except Exception as e:
    logging.exception('An error occurred in the WSGI script: %s', str(e))
    raise
