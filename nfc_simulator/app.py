# nfc_simulator/app.py
import os
import requests
import json
import logging
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO, emit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'nfc-simulator-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
API_URL = os.getenv('API_URL', 'http://backend:8000/api/v1')
DEFAULT_DEVICE_INFO = os.getenv('DEVICE_INFO', 'NFC Simulator')
DEFAULT_LOCATION = os.getenv('LOCATION', 'Main Entrance')

# Store simulated locks
locks = []

# Store verification history
verification_history = []

@app.route('/')
def index():
    """Render the main NFC simulator interface"""
    return render_template('index.html', locks=locks, history=verification_history)

@app.route('/locks', methods=['GET', 'POST'])
def manage_locks():
    """Manage simulated locks"""
    if request.method == 'POST':
        lock_id = request.form.get('lock_id')
        location = request.form.get('location', DEFAULT_LOCATION)
        description = request.form.get('description', 'Room Lock')
        
        if not lock_id:
            flash('Lock ID is required', 'error')
            return redirect(url_for('manage_locks'))
        
        # Check if lock already exists
        for lock in locks:
            if lock['lock_id'] == lock_id:
                flash(f'Lock ID {lock_id} already exists', 'error')
                return redirect(url_for('manage_locks'))
        
        # Add new lock
        locks.append({
            'lock_id': lock_id,
            'location': location,
            'description': description,
            'created_at': datetime.now().isoformat()
        })
        flash(f'Lock {lock_id} added successfully', 'success')
        return redirect(url_for('manage_locks'))
    
    return render_template('locks.html', locks=locks)

@app.route('/locks/<lock_id>/delete', methods=['POST'])
def delete_lock(lock_id):
    """Delete a simulated lock"""
    global locks
    locks = [lock for lock in locks if lock['lock_id'] != lock_id]
    flash(f'Lock {lock_id} deleted successfully', 'success')
    return redirect(url_for('manage_locks'))

@app.route('/simulate', methods=['GET', 'POST'])
def simulate_nfc():
    """Simulate NFC authentication"""
    if request.method == 'POST':
        key_uuid = request.form.get('key_uuid')
        lock_id = request.form.get('lock_id')
        device_info = request.form.get('device_info', DEFAULT_DEVICE_INFO)
        location = request.form.get('location', DEFAULT_LOCATION)
        
        if not key_uuid or not lock_id:
            flash('Key UUID and Lock ID are required', 'error')
            return redirect(url_for('simulate_nfc'))
        
        try:
            # Verify key with the backend API
            response = requests.post(
                f"{API_URL}/verify/key",
                json={
                    'key_uuid': key_uuid,
                    'lock_id': lock_id,
                    'device_info': device_info,
                    'location': location
                }
            )
            
            result = response.json()
            
            # Add to verification history
            verification_entry = {
                'timestamp': datetime.now().isoformat(),
                'key_uuid': key_uuid,
                'lock_id': lock_id,
                'result': result,
                'status': 'success' if result.get('is_valid', False) else 'error'
            }
            verification_history.insert(0, verification_entry)
            
            # Keep history limited to last 100 entries
            if len(verification_history) > 100:
                verification_history.pop()
            
            # Emit event to connected clients
            socketio.emit('verification_result', verification_entry)
            
            return render_template(
                'simulate.html',
                locks=locks,
                result=result,
                form_data={
                    'key_uuid': key_uuid,
                    'lock_id': lock_id,
                    'device_info': device_info,
                    'location': location
                }
            )
            
        except requests.RequestException as e:
            logger.error(f"Error verifying key: {e}")
            flash(f'Error communicating with API: {str(e)}', 'error')
            return redirect(url_for('simulate_nfc'))
    
    # For GET requests, show the form
    lock_id = request.args.get('lock_id', '')
    return render_template('simulate.html', locks=locks, lock_id=lock_id)

@app.route('/api/verify', methods=['POST'])
def api_verify_key():
    """API endpoint for NFC key verification"""
    data = request.json
    if not data or not data.get('key_uuid') or not data.get('lock_id'):
        return jsonify({
            'error': 'Missing required fields',
            'details': 'key_uuid and lock_id are required'
        }), 400
    
    try:
        # Verify key with the backend API
        response = requests.post(
            f"{API_URL}/verify/key",
            json={
                'key_uuid': data.get('key_uuid'),
                'lock_id': data.get('lock_id'),
                'device_info': data.get('device_info', DEFAULT_DEVICE_INFO),
                'location': data.get('location', DEFAULT_LOCATION)
            }
        )
        
        result = response.json()
        
        # Add to verification history
        verification_entry = {
            'timestamp': datetime.now().isoformat(),
            'key_uuid': data.get('key_uuid'),
            'lock_id': data.get('lock_id'),
            'result': result,
            'status': 'success' if result.get('is_valid', False) else 'error'
        }
        verification_history.insert(0, verification_entry)
        
        # Keep history limited to last 100 entries
        if len(verification_history) > 100:
            verification_history.pop()
        
        # Emit event to connected clients
        socketio.emit('verification_result', verification_entry)
        
        return jsonify(result)
        
    except requests.RequestException as e:
        logger.error(f"Error verifying key: {e}")
        return jsonify({
            'error': 'API communication error',
            'details': str(e)
        }), 500

@app.route('/history')
def view_history():
    """View verification history"""
    return render_template('history.html', history=verification_history)

@app.route('/history/clear', methods=['POST'])
def clear_history():
    """Clear verification history"""
    global verification_history
    verification_history = []
    flash('History cleared successfully', 'success')
    return redirect(url_for('view_history'))

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected')

@socketio.on('scan_key')
def handle_scan_key(data):
    """Handle key scanning event from client"""
    key_uuid = data.get('key_uuid')
    lock_id = data.get('lock_id')
    if key_uuid and lock_id:
        logger.info(f'Scanning key {key_uuid} for lock {lock_id}')
        
        try:
            # Verify key with the backend API
            response = requests.post(
                f"{API_URL}/verify/key",
                json={
                    'key_uuid': key_uuid,
                    'lock_id': lock_id,
                    'device_info': data.get('device_info', DEFAULT_DEVICE_INFO),
                    'location': data.get('location', DEFAULT_LOCATION)
                }
            )
            
            result = response.json()
            
            # Add to verification history
            verification_entry = {
                'timestamp': datetime.now().isoformat(),
                'key_uuid': key_uuid,
                'lock_id': lock_id,
                'result': result,
                'status': 'success' if result.get('is_valid', False) else 'error'
            }
            verification_history.insert(0, verification_entry)
            
            # Keep history limited to last 100 entries
            if len(verification_history) > 100:
                verification_history.pop()
            
            # Emit result to all clients
            emit('verification_result', verification_entry, broadcast=True)
            
        except requests.RequestException as e:
            logger.error(f"Error verifying key: {e}")
            emit('error', {'message': f'Error communicating with API: {str(e)}'})
    else:
        emit('error', {'message': 'Key UUID and Lock ID are required'})

if __name__ == '__main__':
    # Add some default locks
    if not locks:
        locks.append({
            'lock_id': 'LOCK-A123B456',
            'location': 'Main Entrance',
            'description': 'Front Door',
            'created_at': datetime.now().isoformat()
        })
        locks.append({
            'lock_id': 'LOCK-B789C012',
            'location': 'Room 101',
            'description': 'Standard Room',
            'created_at': datetime.now().isoformat()
        })
        locks.append({
            'lock_id': 'LOCK-D345E678',
            'location': 'Room 201',
            'description': 'Deluxe Room',
            'created_at': datetime.now().isoformat()
        })
    
    # Run the Flask application with SocketIO
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f'Starting NFC Simulator on {host}:{port} (debug={debug})')
    socketio.run(app, host=host, port=port, debug=debug)
