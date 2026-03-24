from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
import cv2
import numpy as np
from datetime import datetime, date
import configparser
try:
    from attendance_system import AttendanceSystem
except Exception:
    from simple_attendance import SimpleAttendanceSystem as AttendanceSystem
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize system
config = configparser.ConfigParser()
config.read('config.ini')
attendance_system = AttendanceSystem()

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register')
def register():
    """Student registration page"""
    return render_template('register.html')

@app.route('/register_student', methods=['POST'])
def register_student():
    """Handle student registration"""
    name = request.form.get('name')
    roll_number = request.form.get('roll_number')
    email = request.form.get('email')
    
    if not name or not roll_number:
        flash('Name and roll number are required!', 'error')
        return redirect(url_for('register'))
    
    success, message = attendance_system.register_new_student(name, roll_number, email)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('register'))

@app.route('/attendance')
def attendance():
    """Attendance marking page"""
    return render_template('attendance.html')

@app.route('/start_session')
def start_session():
    """Start attendance session"""
    return render_template('session.html')

@app.route('/api/session_status')
def session_status():
    """Get session status (for AJAX polling)"""
    # This would be implemented with actual session tracking
    return jsonify({'status': 'active', 'recognized': 0})

@app.route('/api/quick_stats')
def quick_stats():
    """Quick stats for home page cards"""
    try:
        today_attendance = attendance_system.get_today_attendance()
        all_students = attendance_system.view_all_students()

        total_students = len(all_students)
        present_today = len([a for a in today_attendance if a[4] == 'present'])
        late_today = len([a for a in today_attendance if a[4] == 'late'])
        attendance_rate = ((present_today + late_today) / total_students * 100) if total_students > 0 else 0

        return jsonify({
            'total_students': total_students,
            'present_today': present_today,
            'late_today': late_today,
            'attendance_rate': attendance_rate
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/view_attendance')
def view_attendance():
    """View attendance records"""
    selected_date = request.args.get('date', date.today().isoformat())
    attendance_data = attendance_system.get_today_attendance()
    
    return render_template('view_attendance.html', 
                         attendance=attendance_data, 
                         selected_date=selected_date)

@app.route('/students')
def students():
    """View all registered students"""
    students_list = attendance_system.view_all_students()
    return render_template('students.html', students=students_list)

@app.route('/reports')
def reports():
    """Generate reports page"""
    return render_template('reports.html')

@app.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate attendance report"""
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    if not start_date or not end_date:
        flash('Start date and end date are required!', 'error')
        return redirect(url_for('reports'))
    
    report_data = attendance_system.generate_attendance_report(start_date, end_date)
    
    return render_template('report_results.html', 
                         report=report_data, 
                         start_date=start_date, 
                         end_date=end_date)

@app.route('/export/<date>')
def export_attendance(date):
    """Export attendance to CSV"""
    try:
        filename = attendance_system.export_attendance_to_csv(date)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        flash(f'Error exporting attendance: {str(e)}', 'error')
        return redirect(url_for('view_attendance'))

@app.route('/api/camera_feed')
def camera_feed():
    """Provide camera feed for web interface"""
    def generate_frames():
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
    
    return app.response_class(generate_frames(), 
                             mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/recognize_face', methods=['POST'])
def recognize_face():
    """API endpoint for face recognition"""
    try:
        # Get image data from request
        image_data = request.json.get('image')
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode base64 image
        image_data = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Recognize faces
        face_locations, names, roll_numbers = attendance_system.face_recognition.recognize_face(frame)
        
        # Mark attendance for recognized faces
        recognized_students = []
        for name, roll_number in zip(names, roll_numbers):
            if name != "Unknown":
                attendance_system.mark_attendance_callback(roll_number)
                recognized_students.append({'name': name, 'roll_number': roll_number})
        
        return jsonify({
            'success': True,
            'recognized': recognized_students,
            'face_locations': face_locations
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/manual_attendance', methods=['GET', 'POST'])
def manual_attendance():
    """Manual attendance marking"""
    if request.method == 'POST':
        roll_number = request.form.get('roll_number')
        status = request.form.get('status', 'present')
        
        success, message = attendance_system.manual_attendance_mark(roll_number, status)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('manual_attendance'))
    
    return render_template('manual_attendance.html')

@app.route('/delete_student/<roll_number>', methods=['POST'])
def delete_student(roll_number):
    """Delete a student"""
    try:
        attendance_system.delete_student(roll_number)
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting student: {str(e)}', 'error')
    
    return redirect(url_for('students'))

@app.route('/edit_student/<roll_number>', methods=['GET', 'POST'])
def edit_student(roll_number):
    """Edit student information"""
    student = attendance_system.db_manager.get_student_by_roll(roll_number)
    
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('students'))
    
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_email = request.form.get('email')
        
        try:
            attendance_system.update_student_info(roll_number, new_name, new_email)
            flash('Student information updated successfully!', 'success')
            return redirect(url_for('students'))
        except Exception as e:
            flash(f'Error updating student: {str(e)}', 'error')
    
    return render_template('edit_student.html', student=student)

@app.route('/dashboard')
def dashboard():
    """Dashboard with statistics"""
    # Get today's attendance
    today_attendance = attendance_system.get_today_attendance()
    
    # Get total students
    all_students = attendance_system.view_all_students()
    
    # Calculate statistics
    total_students = len(all_students)
    present_today = len([a for a in today_attendance if a[4] == 'present'])
    late_today = len([a for a in today_attendance if a[4] == 'late'])
    absent_today = total_students - present_today - late_today
    
    stats = {
        'total_students': total_students,
        'present_today': present_today,
        'late_today': late_today,
        'absent_today': absent_today,
        'attendance_rate': (present_today + late_today) / total_students * 100 if total_students > 0 else 0
    }
    
    return render_template('dashboard.html', stats=stats, recent_attendance=today_attendance[:10])

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Get configuration
    host = config.get('WEB_INTERFACE', 'host')
    port = config.getint('WEB_INTERFACE', 'port')
    debug = config.getboolean('WEB_INTERFACE', 'debug')
    
    print(f"Starting web server at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
