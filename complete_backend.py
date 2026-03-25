from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_cors import CORS
import os
import cv2
import numpy as np
from datetime import datetime, date
import configparser
import base64
import logging
from functools import wraps
import traceback

# Import our complete attendance system
from complete_attendance_system import CompleteAttendanceSystem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'auratrack_complete_backend_2024_secure'

# Enable CORS for API endpoints
CORS(app)

# Initialize system
config = configparser.ConfigParser()
config.read('config.ini')
attendance_system = CompleteAttendanceSystem()

# Error handling decorator
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e}")
            logger.error(traceback.format_exc())
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
            else:
                flash(f'An error occurred: {str(e)}', 'error')
                return redirect(url_for('index'))
    return decorated_function

# ==================== MAIN ROUTES ====================

@app.route('/')
@handle_errors
def index():
    """Home page with system overview"""
    stats = attendance_system.get_attendance_stats()
    recent_attendance = attendance_system.get_recent_attendance(5)
    return render_template('index.html', stats=stats, recent_attendance=recent_attendance)

@app.route('/register')
@handle_errors
def register():
    """Employee registration page"""
    return render_template('register.html')

@app.route('/register_student', methods=['POST'])
@handle_errors
def register_student():
    """Handle employee registration with face data"""
    name = request.form.get('name', '').strip()
    roll_number = request.form.get('roll_number', '').strip()
    email = request.form.get('email', '').strip()
    face_image_data = request.form.get('face_image_data', '').strip()
    
    # Validate required fields
    if not name:
        flash('Name is required!', 'error')
        return redirect(url_for('register'))
    
    if not roll_number:
        flash('Employee ID is required!', 'error')
        return redirect(url_for('register'))
    
    # Register student
    success, message = attendance_system.register_student_with_face(
        name, roll_number, email if email else None, face_image_data if face_image_data else None
    )
    
    if success:
        flash(message, 'success')
        logger.info(f"Student registered: {name} ({roll_number})")
    else:
        flash(message, 'error')
        logger.warning(f"Registration failed: {name} ({roll_number}) - {message}")
    
    return redirect(url_for('register'))

@app.route('/attendance')
@handle_errors
def attendance():
    """Attendance marking page"""
    return render_template('attendance.html')

@app.route('/dashboard')
@handle_errors
def dashboard():
    """Analytics dashboard"""
    stats = attendance_system.get_attendance_stats()
    recent_attendance = attendance_system.get_recent_attendance(20)
    return render_template('dashboard.html', stats=stats, recent_attendance=recent_attendance)

@app.route('/students')
@handle_errors
def students():
    """View all registered employees"""
    students_list = attendance_system.get_all_students()
    return render_template('students.html', students=students_list)

@app.route('/view_attendance')
@handle_errors
def view_attendance():
    """View attendance records"""
    selected_date = request.args.get('date', date.today().isoformat())
    attendance_data = attendance_system.get_recent_attendance(50)
    
    # Filter by selected date if provided
    if selected_date != date.today().isoformat():
        attendance_data = [record for record in attendance_data if record[2] == selected_date]
    
    return render_template('view_attendance.html', 
                         attendance=attendance_data, 
                         selected_date=selected_date)

@app.route('/reports')
@handle_errors
def reports():
    """Generate reports page"""
    return render_template('reports.html')

@app.route('/generate_report', methods=['POST'])
@handle_errors
def generate_report():
    """Generate attendance report"""
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')
    
    if not start_date or not end_date:
        flash('Start date and end date are required!', 'error')
        return redirect(url_for('reports'))
    
    report_data = attendance_system.generate_attendance_report(start_date, end_date)
    
    return render_template('report_results.html', 
                         report=report_data, 
                         start_date=start_date, 
                         end_date=end_date)

@app.route('/export/<date>')
@handle_errors
def export_attendance(date):
    """Export attendance to CSV"""
    try:
        filename = attendance_system.export_attendance_to_csv(date)
        if filename and os.path.exists(filename):
            return send_file(filename, as_attachment=True)
        else:
            flash('No data found for the specified date', 'error')
            return redirect(url_for('view_attendance'))
    except Exception as e:
        flash(f'Error exporting attendance: {str(e)}', 'error')
        return redirect(url_for('view_attendance'))

@app.route('/delete_student/<roll_number>', methods=['POST'])
@handle_errors
def delete_student(roll_number):
    """Delete a student"""
    success, message = attendance_system.delete_student(roll_number)
    
    if success:
        flash(message, 'success')
        logger.info(f"Student deleted: {roll_number}")
    else:
        flash(message, 'error')
        logger.warning(f"Student deletion failed: {roll_number} - {message}")
    
    return redirect(url_for('students'))

@app.route('/edit_student/<roll_number>', methods=['GET', 'POST'])
@handle_errors
def edit_student(roll_number):
    """Edit student information"""
    student = attendance_system.get_student_by_roll_number(roll_number)
    
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('students'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        
        if not name:
            flash('Name is required!', 'error')
            return render_template('edit_student.html', student=student)
        
        success, message = attendance_system.update_student(roll_number, name, email if email else None)
        
        if success:
            flash(message, 'success')
            logger.info(f"Student updated: {roll_number}")
            return redirect(url_for('students'))
        else:
            flash(message, 'error')
            logger.warning(f"Student update failed: {roll_number} - {message}")
    
    return render_template('edit_student.html', student=student)

# ==================== API ENDPOINTS ====================

@app.route('/api/recognize_face', methods=['POST'])
@handle_errors
def recognize_face():
    """Face recognition API with proper error handling"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        image_data = data.get('image', '')
        
        if not image_data:
            return jsonify({
                'success': False,
                'error': 'No image data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Use the complete face recognition system
        result = attendance_system.recognize_face_real(image_data)
        
        if isinstance(result, dict):
            return jsonify({
                'success': True,
                'recognized': [{
                    'name': result['name'],
                    'roll_number': result['roll_number'],
                    'confidence': result['confidence']
                }],
                'face_locations': [[100, 100, 200, 200]],  # Mock face location
                'message': result.get('message', 'Face recognized successfully'),
                'timestamp': result.get('timestamp', datetime.now().isoformat())
            })
        else:
            # Handle tuple return format
            if isinstance(result, tuple) and len(result) == 3:
                name, confidence, message = result
                if name and confidence > 0:
                    return jsonify({
                        'success': True,
                        'recognized': [{
                            'name': name,
                            'confidence': confidence,
                            'message': message
                        }],
                        'face_locations': [[100, 100, 200, 200]],
                        'message': message,
                        'timestamp': datetime.now().isoformat()
                    })
            
            return jsonify({
                'success': False,
                'recognized': [],
                'face_locations': [],
                'message': result if isinstance(result, str) else 'No face recognized',
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Face recognition API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/session_status')
@handle_errors
def session_status():
    """Get session status and real-time statistics"""
    try:
        stats = attendance_system.get_attendance_stats()
        return jsonify({
            'status': 'active',
            'recognized': stats['present_today'],
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Session status API error: {e}")
        return jsonify({
            'status': 'error',
            'recognized': 0,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/quick_stats')
@handle_errors
def quick_stats():
    """Quick statistics for dashboard"""
    try:
        stats = attendance_system.get_attendance_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Quick stats API error: {e}")
        return jsonify({
            'total_students': 0,
            'present_today': 0,
            'late_today': 0,
            'absent_today': 0,
            'attendance_rate': 0,
            'error': str(e)
        }), 500

@app.route('/api/camera_feed')
@handle_errors
def camera_feed():
    """Provide camera feed for web interface"""
    def generate_frames():
        try:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            while True:
                success, frame = cap.read()
                if not success:
                    break
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            cap.release()
        except Exception as e:
            logger.error(f"Camera feed error: {e}")
    
    return app.response_class(generate_frames(), 
                             mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/system_health')
@handle_errors
def system_health():
    """Get system health information"""
    try:
        health = attendance_system.get_system_health()
        return jsonify(health)
    except Exception as e:
        logger.error(f"System health API error: {e}")
        return jsonify({
            'database_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/students')
@handle_errors
def api_students():
    """Get all students as JSON"""
    try:
        students = attendance_system.get_all_students()
        students_data = []
        
        for student in students:
            students_data.append({
                'id': student[0],
                'name': student[1],
                'roll_number': student[2],
                'email': student[3],
                'registration_date': student[4],
                'face_data_path': student[5],
                'face_registered': bool(student[6])
            })
        
        return jsonify({
            'success': True,
            'students': students_data,
            'count': len(students_data)
        })
    except Exception as e:
        logger.error(f"Students API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/attendance')
@handle_errors
def api_attendance():
    """Get attendance records as JSON"""
    try:
        limit = request.args.get('limit', 50, type=int)
        attendance = attendance_system.get_recent_attendance(limit)
        
        attendance_data = []
        for record in attendance:
            attendance_data.append({
                'name': record[0],
                'roll_number': record[1],
                'date': record[2],
                'check_in_time': record[3],
                'check_out_time': record[4],
                'status': record[5],
                'confidence': record[6]
            })
        
        return jsonify({
            'success': True,
            'attendance': attendance_data,
            'count': len(attendance_data)
        })
    except Exception as e:
        logger.error(f"Attendance API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

# ==================== UTILITY ROUTES ====================

@app.route('/camera_test')
@handle_errors
def camera_test():
    """Camera test page for debugging"""
    return render_template('camera_test.html')

@app.route('/health')
@handle_errors
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

# ==================== MAIN EXECUTION ====================

if __name__ == '__main__':
    try:
        # Create necessary directories
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static', exist_ok=True)
        os.makedirs('known_faces', exist_ok=True)
        os.makedirs('captured_images', exist_ok=True)
        
        # Get configuration (Render uses environment variables)
        host = os.environ.get('HOST', '127.0.0.1')
        port = int(os.environ.get('PORT', 8080))
        debug = os.environ.get('FLASK_ENV', 'development') == 'development'
        
        logger.info(f"Starting AuraTrack backend server at http://{host}:{port}")
        logger.info(f"Debug mode: {debug}")
        logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
        
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"Error starting server: {e}")
    finally:
        logger.info("AuraTrack backend server stopped")
