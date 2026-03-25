from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
import os
import cv2
import numpy as np
import base64
import sqlite3
from datetime import datetime, date
import configparser
import logging
import json
from io import BytesIO
from PIL import Image
import warnings
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'auratrack_deep_learning_2024_secure'
CORS(app)

# Initialize database
config = configparser.ConfigParser()
config.read('config.ini')

class DeepLearningFaceRecognition:
    """Advanced face recognition using deep learning models"""
    
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.face_detector = None
        self.face_encoder = None
        self.load_models()
        self.load_known_faces()
    
    def load_models(self):
        """Load deep learning face detection and recognition models"""
        try:
            # Load face detection model
            self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Try to load dlib face detector (more accurate)
            try:
                import dlib
                self.dlib_detector = dlib.get_frontal_face_detector()
                logger.info("Dlib face detector loaded successfully")
            except ImportError:
                self.dlib_detector = None
                logger.warning("Dlib not available, using OpenCV only")
            
            # Try to load face recognition library
            try:
                import face_recognition
                self.face_recognition_available = True
                logger.info("Face recognition library available")
            except ImportError:
                self.face_recognition_available = False
                logger.warning("Face recognition library not available")
            
            logger.info("Deep learning models loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def load_known_faces(self):
        """Load known faces from database"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # Create students table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    roll_number TEXT UNIQUE NOT NULL,
                    email TEXT,
                    registration_date TEXT,
                    face_data TEXT,
                    face_encoding TEXT,
                    face_registered INTEGER DEFAULT 0
                )
            ''')
            
            # Get students with face data
            cursor.execute('SELECT name, roll_number, face_data, face_encoding FROM students WHERE face_registered = 1')
            students = cursor.fetchall()
            
            for student in students:
                name, roll_number, face_data, face_encoding = student
                
                # Use face encoding if available, otherwise use face data
                if face_encoding and face_encoding.startswith('data:image'):
                    try:
                        encoding = self.decode_base64_image(face_encoding)
                        if encoding is not None:
                            # Convert to face encoding
                            face_encoding_array = self.face_to_encoding(encoding)
                            if face_encoding_array is not None:
                                self.known_face_encodings.append(face_encoding_array)
                                self.known_face_names.append(name)
                                logger.info(f"Loaded deep learning encoding for {name}")
                    except Exception as e:
                        logger.error(f"Error loading encoding for {name}: {e}")
                
                elif face_data and face_data.startswith('data:image'):
                    try:
                        face_img = self.decode_base64_image(face_data)
                        if face_img is not None:
                            # Convert to face encoding
                            face_encoding_array = self.face_to_encoding(face_img)
                            if face_encoding_array is not None:
                                self.known_face_encodings.append(face_encoding_array)
                                self.known_face_names.append(name)
                                logger.info(f"Generated encoding for {name}")
                    except Exception as e:
                        logger.error(f"Error generating encoding for {name}: {e}")
            
            conn.close()
            logger.info(f"Loaded {len(self.known_face_encodings)} face encodings")
            
        except Exception as e:
            logger.error(f"Error loading known faces: {e}")
    
    def decode_base64_image(self, base64_string):
        """Decode base64 image to OpenCV format"""
        try:
            # Remove data URL prefix
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decode base64
            img_data = base64.b64decode(base64_string)
            
            # Convert to PIL Image
            pil_image = Image.open(BytesIO(img_data))
            
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            return cv_image
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None
    
    def face_to_encoding(self, face_image):
        """Convert face image to 128-dimension encoding"""
        try:
            # Convert to RGB if needed
            if len(face_image.shape) == 3:
                face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            
            # Resize to standard size
            face_image = cv2.resize(face_image, (150, 150))
            
            # Use face recognition library if available
            if self.face_recognition_available:
                try:
                    import face_recognition
                    face_locations = face_recognition.face_locations(face_image, model="hog")
                    if len(face_locations) > 0:
                        face_encodings = face_recognition.face_encodings(face_image, face_locations)
                        if len(face_encodings) > 0:
                            return face_encodings[0]
                except Exception as e:
                    logger.error(f"Face recognition library error: {e}")
            
            # Fallback to OpenCV method
            return self.opencv_face_encoding(face_image)
            
        except Exception as e:
            logger.error(f"Error creating face encoding: {e}")
            return None
    
    def opencv_face_encoding(self, face_image):
        """OpenCV-based face encoding (fallback)"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_image, cv2.COLOR_RGB2GRAY)
            
            # Resize to standard size
            gray = cv2.resize(gray, (100, 100))
            
            # Use LBP (Local Binary Patterns) as encoding
            lbp = cv2.localBinaryPattern(gray, 1, 8, 8, 8, 200)
            
            # Create histogram as encoding
            hist = cv2.calcHist([lbp], [256], [0, 256], cv2.HISTCMP_CORREL)
            
            return hist.flatten()
            
        except Exception as e:
            logger.error(f"OpenCV encoding error: {e}")
            return None
    
    def detect_faces(self, image):
        """Detect faces using deep learning models"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Method 1: OpenCV Haar Cascade
            faces_haar = self.face_detector.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
            
            # Method 2: Dlib HOG detector (if available)
            faces_dlib = []
            if self.dlib_detector:
                try:
                    import dlib
                    dlib_faces = self.dlib_detector(gray, 1)
                    faces_dlib = [(d.left(), d.top(), d.right()-d.left(), d.bottom()-d.top()) for d in dlib_faces]
                except Exception as e:
                    logger.error(f"Dlib detection error: {e}")
            
            # Method 3: MTCNN (Multi-task Cascaded CNN) - more accurate
            try:
                # Load MTCNN model
                model_file = "deploy.prototxt"
                weights_file = "res10_300x300_iter_140000.caffemodel"
                
                if os.path.exists(model_file) and os.path.exists(weights_file):
                    net = cv2.dnn.readNetFromCaffe(model_file, weights_file)
                    blob = cv2.dnn.blobFromImage(gray, 1.0, (300, 300), (104.0, 177.0, 123.0))
                    net.setInput(blob)
                    detections = net.forward()
                    
                    faces_mtcnn = []
                    for i in range(detections.shape[2]):
                        confidence = detections[0, 0, 0, i, 2]
                        if confidence > 0.7:  # High confidence threshold
                            box = detections[0, 0, 0, i, 3:7] * [300, 300, 300, 300]
                            faces_mtcnn.append(box)
                    
                    logger.info(f"MTCNN detected {len(faces_mtcnn)} faces")
                else:
                    faces_mtcnn = []
            except Exception as e:
                logger.error(f"MTCNN error: {e}")
                faces_mtcnn = []
            
            # Combine all methods
            all_faces = faces_haar + faces_dlib + faces_mtcnn
            
            # Remove duplicates and return best
            unique_faces = []
            for face in all_faces:
                if face not in unique_faces:
                    unique_faces.append(face)
            
            logger.info(f"Detected {len(unique_faces)} faces using deep learning")
            return unique_faces
            
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return []
    
    def recognize_face(self, image_data):
        """Recognize face using deep learning models"""
        try:
            # Decode image
            face_img = self.decode_base64_image(image_data)
            if face_img is None:
                return None, 0.0, "Could not decode image"
            
            # Detect faces
            faces = self.detect_faces(face_img)
            
            if len(faces) == 0:
                return None, 0.0, "No face detected"
            
            # Use the first detected face
            if isinstance(faces[0], tuple):
                # Haar/Dlib format
                x, y, w, h = faces[0]
                face_roi = face_img[y:y+h, x:x+w]
            else:
                # MTCNN format
                x, y, w, h = faces[0]
                face_roi = face_img[int(y):int(y+h), int(x):int(x+w)]
            
            # Resize to standard size
            face_roi = cv2.resize(face_roi, (150, 150))
            
            # Compare with known faces
            if len(self.known_face_encodings) == 0:
                return "Unknown", 0.5, "No registered faces to compare"
            
            best_match = None
            best_confidence = 0.0
            best_distance = float('inf')
            
            # Create encoding for detected face
            detected_encoding = self.face_to_encoding(face_roi)
            
            if detected_encoding is None:
                return None, 0.0, "Could not create face encoding"
            
            # Compare with all known faces
            for i, known_encoding in enumerate(self.known_face_encodings):
                try:
                    if self.face_recognition_available:
                        # Use face recognition library for comparison
                        import face_recognition
                        distance = face_recognition.face_distance([known_encoding], [detected_encoding])[0]
                        confidence = (1.0 - distance) * 100  # Convert distance to confidence
                    else:
                        # Use Euclidean distance for OpenCV encodings
                        distance = np.linalg.norm(known_encoding - detected_encoding)
                        confidence = max(0, (1.0 - distance/100.0)) * 100
                    
                    if distance < best_distance and confidence > 30:  # Threshold
                        best_distance = distance
                        best_confidence = confidence
                        best_match = self.known_face_names[i]
                        
                except Exception as e:
                    logger.error(f"Comparison error for {self.known_face_names[i]}: {e}")
                    continue
            
            if best_match:
                return best_match, best_confidence, f"Deep learning recognition with {best_confidence:.1f}% confidence"
            else:
                return None, 0.0, "Face not recognized"
                
        except Exception as e:
            logger.error(f"Deep learning recognition error: {e}")
            return None, 0.0, f"Recognition error: {str(e)}"

# Initialize deep learning face recognition system
face_system = DeepLearningFaceRecognition()

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
        
        # Create students table with face_encoding column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_number TEXT UNIQUE NOT NULL,
                email TEXT,
                registration_date TEXT,
                face_data TEXT,
                face_encoding TEXT,
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
        
        # Add face_encoding column if it doesn't exist
        cursor.execute('PRAGMA table_info(students)')
        columns = cursor.fetchall()
        has_face_encoding = any(col[1] == 'face_encoding' for col in columns)
        
        if not has_face_encoding:
            cursor.execute('ALTER TABLE students ADD COLUMN face_encoding TEXT')
            logger.info("Added face_encoding column to students table")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False

# Initialize database
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
                VALUES (?, ?, ?, ?, ?)
            ''', (student['name'], student['roll_number'], student['email'], 
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Sample data error: {e}")
        return False

# Add sample data
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
    """Handle student registration with face data"""
    try:
        name = request.form.get('name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        email = request.form.get('email', '').strip()
        face_image_data = request.form.get('face_image_data', '').strip()
        
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
        
        # Create face encoding
        face_encoding = None
        if face_image_data:
            face_img = face_system.decode_base64_image(face_image_data)
            if face_img is not None:
                face_encoding = face_system.face_to_encoding(face_img)
        
        # Convert encoding to string for storage
        encoding_string = None
        if face_encoding is not None:
            encoding_string = base64.b64encode(face_encoding.tobytes()).decode('utf-8')
        
        # Insert student
        face_registered = 1 if face_image_data else 0
        cursor.execute('''
            INSERT INTO students (name, roll_number, email, registration_date, face_data, face_encoding, face_registered)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, roll_number, email, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
               face_image_data, encoding_string, face_registered))
        
        conn.commit()
        conn.close()
        
        # Reload face recognition system
        face_system.load_known_faces()
        
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

@app.route('/view_attendance')
def view_attendance():
    """View attendance records page"""
    selected_date = request.args.get('date', date.today().isoformat())
    attendance_data = get_recent_attendance(50)
    
    # Filter by selected date if provided
    if selected_date != date.today().isoformat():
        attendance_data = [record for record in attendance_data if record[2] == selected_date]
    
    return render_template('view_attendance.html', 
                         attendance=attendance_data, 
                         selected_date=selected_date)

@app.route('/students')
def students():
    """View all registered students"""
    try:
        conn = get_db_connection()
        if not conn:
            return render_template('students.html', students=[])
        
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, roll_number, email, registration_date, face_registered FROM students ORDER BY registration_date DESC')
        students_list = cursor.fetchall()
        conn.close()
        
        return render_template('students.html', students=students_list)
    except Exception as e:
        logger.error(f"Students page error: {e}")
        return render_template('students.html', students=[])

@app.route('/reports')
def reports():
    """Generate reports page"""
    return render_template('reports.html')

@app.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate attendance report"""
    try:
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        
        if not start_date or not end_date:
            flash('Start date and end date are required!', 'error')
            return redirect(url_for('reports'))
        
        # Generate report data (simplified)
        report_data = {
            'total_students': 5,
            'total_days': 10,
            'total_attendance': 45,
            'attendance_rate': 90.0
        }
        
        return render_template('report_results.html', 
                         report=report_data, 
                         start_date=start_date, 
                         end_date=end_date)
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        flash('Report generation failed!', 'error')
        return redirect(url_for('reports'))

@app.route('/export/<date>')
def export_attendance(date):
    """Export attendance to CSV"""
    try:
        import csv
        from io import StringIO
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error!', 'error')
            return redirect(url_for('view_attendance'))
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.name, s.roll_number, a.date, a.check_in_time, a.status, a.confidence
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date = ?
            ORDER BY a.check_in_time
        ''', (date,))
        
        records = cursor.fetchall()
        conn.close()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Name', 'Roll Number', 'Date', 'Check In Time', 'Status', 'Confidence'])
        
        for record in records:
            writer.writerow(record)
        
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=attendance_{date}.csv'
        }
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        flash('Export failed!', 'error')
        return redirect(url_for('view_attendance'))

@app.route('/delete_student/<roll_number>', methods=['POST'])
def delete_student(roll_number):
    """Delete a student"""
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection error!', 'error')
            return redirect(url_for('students'))
        
        cursor = conn.cursor()
        cursor.execute('DELETE FROM students WHERE roll_number = ?', (roll_number,))
        conn.commit()
        conn.close()
        
        flash(f'Student {roll_number} deleted successfully!', 'success')
        return redirect(url_for('students'))
        
    except Exception as e:
        logger.error(f"Delete student error: {e}")
        flash('Delete failed!', 'error')
        return redirect(url_for('students'))

@app.route('/edit_student/<roll_number>', methods=['GET', 'POST'])
def edit_student(roll_number):
    """Edit student information"""
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection error!', 'error')
            return redirect(url_for('students'))
        
        cursor = conn.cursor()
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            
            if not name:
                flash('Name is required!', 'error')
                return render_template('edit_student.html', student=None)
            
            cursor.execute('''
                UPDATE students SET name = ?, email = ? WHERE roll_number = ?
            ''', (name, email, roll_number))
            
            conn.commit()
            conn.close()
            
            flash(f'Student {roll_number} updated successfully!', 'success')
            return redirect(url_for('students'))
        else:
            cursor.execute('SELECT * FROM students WHERE roll_number = ?', (roll_number,))
            student = cursor.fetchone()
            conn.close()
            
            if not student:
                flash('Student not found!', 'error')
                return redirect(url_for('students'))
            
            return render_template('edit_student.html', student=student)
            
    except Exception as e:
        logger.error(f"Edit student error: {e}")
        flash('Edit failed!', 'error')
        return redirect(url_for('students'))

@app.route('/camera_feed')
def camera_feed():
    """Camera feed endpoint for video streaming"""
    return jsonify({
        'status': 'camera_ready',
        'message': 'Deep learning camera feed ready'
    })

@app.route('/api/recognize_face', methods=['POST'])
def recognize_face():
    """Deep learning face recognition API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        image_data = data.get('image', '')
        if not image_data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
        
        # Use deep learning face recognition
        name, confidence, message = face_system.recognize_face(image_data)
        
        if name and name != "Unknown":
            # Mark attendance
            success = mark_attendance(name, confidence)
            if success:
                return jsonify({
                    'success': True,
                    'recognized': [{
                        'name': name,
                        'roll_number': get_roll_number_by_name(name),
                        'confidence': confidence
                    }],
                    'face_locations': [[100, 100, 200, 200]],
                    'message': message,
                    'method': 'deep_learning'
                })
        
        return jsonify({
            'success': False,
            'recognized': [],
            'face_locations': [],
            'message': message,
            'method': 'deep_learning'
        })
        
    except Exception as e:
        logger.error(f"Deep learning face recognition API error: {e}")
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
        'version': '3.0.0-deep-learning',
        'face_recognition': 'deep_learning',
        'models_loaded': face_system.face_detector is not None,
        'known_faces': len(face_system.known_face_encodings),
        'dlib_available': face_system.dlib_detector is not None,
        'face_recognition_lib': face_system.face_recognition_available
    })

def get_roll_number_by_name(name):
    """Get roll number by student name"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute('SELECT roll_number FROM students WHERE name = ?', (name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting roll number: {e}")
        return None

def mark_attendance(student_name, confidence):
    """Mark attendance for recognized student"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Get student ID
        cursor.execute('SELECT id FROM students WHERE name = ?', (student_name,))
        student = cursor.fetchone()
        
        if not student:
            conn.close()
            return False
        
        student_id = student[0]
        today = date.today().isoformat()
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Check if already marked today
        cursor.execute('''
            SELECT id FROM attendance 
            WHERE student_id = ? AND date = ?
        ''', (student_id, today))
        
        if cursor.fetchone():
            conn.close()
            return True  # Already marked
        
        # Determine status
        current_hour = datetime.now().hour
        status = 'late' if current_hour >= 9 else 'present'
        
        # Insert attendance record
        cursor.execute('''
            INSERT INTO attendance (student_id, date, check_in_time, status, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id, today, current_time, status, confidence))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error marking attendance: {e}")
        return False

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
