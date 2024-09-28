import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, send_file, request, redirect, jsonify, url_for
from flask_socketio import SocketIO, emit
from pymongo import MongoClient, errors
from contextlib import contextmanager
import datetime

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Consider moving this to an environment variable

# Initialize SocketIO
socketio = SocketIO(app)

# Configure logging
log_path = 'C:/Users/Aneesh S/OneDrive/Desktop/Sen-Net/SenNet/SenNet.log'
handler = RotatingFileHandler(log_path, maxBytes=100000, backupCount=3)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

@contextmanager
def get_db_connection():
    client = None
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['SenNet_db']
        yield db
    except errors.ServerSelectionTimeoutError as err:
        app.logger.error(f"MongoDB connection error: {err}")
        yield None
    finally:
        if client:
            client.close()

def get_detected_data():
    with get_db_connection() as db:
        if db is None:
            app.logger.error("Failed to get MongoDB connection in get_detected_data")
            return []
        collection = db['detected_issues']
        try:
            data = list(collection.find().sort('timestamp', -1))
            return [{"type": item['type'], "details": item['details'], "timestamp": item['timestamp']} for item in data]
        except Exception as e:
            app.logger.error(f'Error fetching detected data: {e}')
            return []

def insert_detected_issue(issue_type, details):
    with get_db_connection() as db:
        if db is None:
            app.logger.error("Failed to get MongoDB connection in insert_detected_issue")
            return
        collection = db['detected_issues']
        try:
            collection.insert_one({
                'type': issue_type,
                'details': details,
                'timestamp': datetime.datetime.now()
            })
            # Emit update to all connected clients
            socketio.emit('status_update', get_network_status())
        except Exception as e:
            app.logger.error(f'Error inserting issue: {e}')

def clear_detected_data():
    with get_db_connection() as db:
        if db is None:
            app.logger.error("Failed to get MongoDB connection in clear_detected_data")
            return 0
        collection = db['detected_issues']
        try:
            result = collection.delete_many({})
            return result.deleted_count
        except Exception as e:
            app.logger.error(f'Error clearing detected data: {e}')
            return 0

def get_network_status():
    try:
        blacklisted_ips = get_blacklisted_ips()
        ad_sources = get_ad_sources()
        return {'blacklisted_ips': blacklisted_ips, 'ad_sources': ad_sources}
    except Exception as e:
        app.logger.error(f'Error fetching network status: {e}')
        return {'blacklisted_ips': [], 'ad_sources': []}

def get_blacklisted_ips():
    with get_db_connection() as db:
        if db is None:
            app.logger.error("Failed to get MongoDB connection in get_blacklisted_ips")
            return []
        collection = db['blacklisted_ips']
        try:
            ips = list(collection.find())
            return [ip['address'] for ip in ips]
        except Exception as e:
            app.logger.error(f'Error fetching blacklisted IPs: {e}')
            return []


def get_ad_sources():
    with get_db_connection() as db:
        if db is None:
            app.logger.error("Failed to get MongoDB connection in get_ad_sources")
            return []
        collection = db['ad_sources']
        try:
            sources = list(collection.find())
            return [source['url'] for source in sources]
        except Exception as e:
            app.logger.error(f'Error fetching ad sources: {e}')
            return []

@app.route('/')
def home():
    app.logger.info('Home route accessed')
    return render_template('SenNet.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    app.logger.info('Settings route accessed')
    
    if request.method == 'POST':
        # Retrieve settings from form
        debug_mode = 'debug' in request.form
        secret_key = request.form.get('secret_key')
        language = request.form.get('language', 'en')
        max_log_size = int(request.form.get('max_log_size', '100000'))
        notification_settings = 'notifications' in request.form
        allowed_ips = request.form.get('allowed_ips', '')

        # Update application settings
        app.config['DEBUG'] = debug_mode
        app.config['SECRET_KEY'] = secret_key
        app.config['LANGUAGE'] = language
        app.config['MAX_LOG_SIZE'] = max_log_size  # Store in config for later use
        app.config['NOTIFICATIONS_ENABLED'] = notification_settings
        app.config['ALLOWED_IPS'] = allowed_ips
        
        # Update logger handler if applicable
        for handler in app.logger.handlers:
            if hasattr(handler, 'maxBytes'):
                handler.maxBytes = max_log_size
                handler.flush()

        app.logger.info(f"Settings updated - Debug Mode: {debug_mode}, Secret Key: {secret_key}, Language: {language}, Max Log Size: {max_log_size}, Notifications: {notification_settings}, Allowed IPs: {allowed_ips}")

        return redirect(url_for('settings'))

    # Pass current settings to the template
    debug_mode = app.config.get('DEBUG', False)
    secret_key = app.config.get('SECRET_KEY', '')
    language = app.config.get('LANGUAGE', 'en')
    max_log_size = app.config.get('MAX_LOG_SIZE', 100000)
    notification_settings = app.config.get('NOTIFICATIONS_ENABLED', False)
    allowed_ips = app.config.get('ALLOWED_IPS', '')

    return render_template('settings.html', 
                           debug_mode=debug_mode, 
                           secret_key=secret_key, 
                           language=language, 
                           max_log_size=max_log_size, 
                           notification_settings=notification_settings, 
                           allowed_ips=allowed_ips)

@app.route('/reports')
def reports():
    app.logger.info('Reports route accessed')
    try:
        return send_file(log_path, as_attachment=True)
    except Exception as e:
        app.logger.error(f'Error serving log file: {e}')
        return jsonify({'error': 'Error serving log file'}), 500

@app.route('/view-status')
def view_status():
    app.logger.info('View Status route accessed')
    return render_template('Network_Status.html')

@app.route('/check-ip', methods=['GET'])
def check_ip():
    try:
        ip_address = request.args.get('ip')
        if not ip_address:
            return jsonify({'error': 'No IP address provided'}), 400
        
        blacklisted_ips = get_blacklisted_ips()
        is_blacklisted = ip_address in blacklisted_ips
        result = f'{ip_address} is blacklisted.' if is_blacklisted else f'{ip_address} is not blacklisted.'
        
        return jsonify({'ip': ip_address, 'is_blacklisted': is_blacklisted})
    except Exception as e:
        app.logger.error(f'Error in check_ip route: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/view-data')
def view_data():
    app.logger.info('View Data route accessed')
    data = get_detected_data()
    return render_template('Detected_Data.html', data=data)

@app.route('/manage-alerts')
def manage_alerts():
    app.logger.info('Manage Alerts route accessed')
    return render_template('manage_alerts.html')

@app.route('/system-logs', methods=['GET', 'POST'])
def system_logs():
    if request.method == 'POST':
        if 'clear' in request.form:
            try:
                with open(log_path, 'w') as file:
                    file.write('')
                app.logger.info('Log file cleared successfully')
                return redirect('/system-logs')
            except Exception as e:
                app.logger.error(f'Error clearing log file: {e}')
                return jsonify({'error': 'Error clearing log file'}), 500

    try:
        with open(log_path, 'r') as file:
            logs = file.read()
    except Exception as e:
        app.logger.error(f'Error reading log file: {e}')
        logs = 'Error reading log file'
    return render_template('system_logs.html', logs=logs)

@app.route('/test')
def test():
    app.logger.debug('This is a debug message from /test route')
    app.logger.error('This is an error message from /test route')
    return 'Check the log file for messages!'

@app.route('/loglevels')
def loglevels():
    app.logger.debug('Debug level message')
    app.logger.info('Info level message')
    app.logger.warning('Warning level message')
    app.logger.error('Error level message')
    app.logger.critical('Critical level message')
    return 'Log levels have been tested!'

@app.route('/add-issue', methods=['POST'])
def add_issue():
    issue_type = request.form.get('type')
    details = request.form.get('details')
    if issue_type and details:
        insert_detected_issue(issue_type, details)
        app.logger.info(f"Issue added - Type: {issue_type}, Details: {details}")
        return redirect('/view-data')
    else:
        app.logger.warning('Failed to add issue - Missing type or details')
        return jsonify({'error': 'Missing type or details'}), 400

@app.route('/clear-data', methods=['POST'])
def clear_data():
    count = clear_detected_data()
    app.logger.info(f"Cleared {count} detected issues")
    return redirect('/view-data')

@socketio.on('connect')
def handle_connect():
    app.logger.info('Client connected')
    emit('status_update', get_network_status())

@socketio.on('disconnect')
def handle_disconnect():
    app.logger.info('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)
