from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime, date
import configparser
import base64
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'auratrack_minimal_backend_2024_secure'
CORS(app)

# Initialize database
config = configparser.ConfigParser()
config.read('config.ini')

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect('attendance.db')
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_number TEXT UNIQUE NOT NULL,
                email TEXT,
                registration_date TEXT,
                face_registered INTEGER DEFAULT 0
            )
        ''')
        
        # Create attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT NOT NULL,
                check_in_time TEXT,
                check_out_time TEXT,
                status TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False

# Initialize database on startup
init_database()

# Sample data for testing
sample_students = [
    {'name': 'Alice Johnson', 'roll_number': 'EMP001', 'email': 'alice@company.com'},
    {'name': 'Bob Smith', 'roll_number': 'EMP002', 'email': 'bob@company.com'},
    {'name': 'Carol Williams', 'roll_number': 'EMP003', 'email': 'carol@company.com'},
    {'name': 'David Brown', 'roll_number': 'EMP004', 'email': 'david@company.com'},
    {'name': 'Eva Davis', 'roll_number': 'EMP005', 'email': 'eva@company.com'}
]

def add_sample_data():
    """Add sample data to database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        for student in sample_students:
            cursor.execute('''
                INSERT OR IGNORE INTO students (name, roll_number, email, registration_date, face_registered)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student['name'], student['roll_number'], student['email'], 
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Sample data error: {e}")
        return False

# Add sample data on first run
add_sample_data()

@app.route('/')
def index():
    """Home page"""
    stats = get_attendance_stats()
    return render_template('index.html', stats=stats)

@app.route('/register')
def register():
    """Registration page"""
    return render_template('register.html')

@app.route('/register_student', methods=['POST'])
def register_student():
    """Handle student registration"""
    try:
        name = request.form.get('name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        email = request.form.get('email', '').strip()
        
        if not name or not roll_number:
            flash('Name and roll number are required!', 'error')
            return redirect(url_for('register'))
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error!', 'error')
            return redirect(url_for('register'))
        
        cursor = conn.cursor()
        
        # Check if roll number already exists
        cursor.execute('SELECT id FROM students WHERE roll_number = ?', (roll_number,))
        if cursor.fetchone():
            conn.close()
            flash('Roll number already exists!', 'error')
            return redirect(url_for('register'))
        
        # Insert student
        cursor.execute('''
            INSERT INTO students (name, roll_number, email, registration_date, face_registered)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, roll_number, email, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0))
        
        conn.commit()
        conn.close()
        
        flash(f'Student {name} registered successfully!', 'success')
        return redirect(url_for('register'))
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        flash('Registration failed!', 'error')
        return redirect(url_for('register'))

@app.route('/attendance')
def attendance():
    """Attendance marking page"""
    return render_template('attendance.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    stats = get_attendance_stats()
    recent_attendance = get_recent_attendance(10)
    return render_template('dashboard.html', stats=stats, recent_attendance=recent_attendance)

@app.route('/api/recognize_face', methods=['POST'])
def recognize_face():
    """Simple face recognition API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        image_data = data.get('image', '')
        if not image_data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
        
        # Simple mock face recognition (70% success rate)
        import random
        if random.random() > 0.3:
            # Select random student
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name, roll_number FROM students ORDER BY RANDOM() LIMIT 1')
                student = cursor.fetchone()
                conn.close()
                
                if student:
                    # Mark attendance
                    mark_attendance(student[1], random.uniform(0.7, 0.95))
                    
                    return jsonify({
                        'success': True,
                        'recognized': [{
                            'name': student[0],
                            'roll_number': student[1],
                            'confidence': random.uniform(0.7, 0.95)
                        }],
                        'face_locations': [[100, 100, 200, 200]],
                        'message': f'Face recognized: {student[0]}'
                    })
        
        return jsonify({
            'success': False,
            'recognized': [],
            'face_locations': [],
            'message': 'No face detected'
        })
        
    except Exception as e:
        logger.error(f"Face recognition error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/quick_stats')
def quick_stats():
    """Quick statistics API"""
    try:
        stats = get_attendance_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0-minimal'
    })

def get_attendance_stats():
    """Get attendance statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return {'total_students': 0, 'present_today': 0, 'late_today': 0, 'absent_today': 0}
        
        cursor = conn.cursor()
        
        # Total students
        cursor.execute('SELECT COUNT(*) FROM students')
        total_students = cursor.fetchone()[0]
        
        # Present today
        today = date.today().isoformat()
        cursor.execute('SELECT COUNT(*) FROM attendance WHERE date = ?', (today,))
        present_today = cursor.fetchone()[0]
        
        # Late today
        cursor.execute('SELECT COUNT(*) FROM attendance WHERE date = ? AND status = "late"', (today,))
        late_today = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_students': total_students,
            'present_today': present_today,
            'late_today': late_today,
            'absent_today': total_students - present_today,
            'attendance_rate': (present_today / total_students * 100) if total_students > 0 else 0
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {'total_students': 0, 'present_today': 0, 'late_today': 0, 'absent_today': 0}

def get_recent_attendance(limit=10):
    """Get recent attendance records"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.name, s.roll_number, a.date, a.check_in_time, a.status, a.confidence
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            ORDER BY a.date DESC, a.check_in_time DESC
            LIMIT ?
        ''', (limit,))
        
        records = cursor.fetchall()
        conn.close()
        return records
    except Exception as e:
        logger.error(f"Recent attendance error: {e}")
        return []

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"Error starting server: {e}")
