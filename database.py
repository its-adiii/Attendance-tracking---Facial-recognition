import sqlite3
import os
from datetime import datetime, date
import configparser

class DatabaseManager:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.db_file = self.config.get('DATABASE', 'db_file')
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_number TEXT UNIQUE NOT NULL,
                email TEXT,
                face_encoding_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT NOT NULL,
                check_in_time TIMESTAMP,
                check_out_time TIMESTAMP,
                status TEXT DEFAULT 'present',
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_student(self, name, roll_number, email=None, face_encoding_path=None):
        """Add a new student to the database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO students (name, roll_number, email, face_encoding_path)
                VALUES (?, ?, ?, ?)
            ''', (name, roll_number, email, face_encoding_path))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_student_by_roll(self, roll_number):
        """Get student information by roll number"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, roll_number, email, face_encoding_path
            FROM students WHERE roll_number = ?
        ''', (roll_number,))
        
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_all_students(self):
        """Get all students from database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, roll_number, email, face_encoding_path
            FROM students ORDER BY roll_number
        ''')
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def mark_attendance(self, student_id, check_in_time=None, status='present'):
        """Mark attendance for a student"""
        if check_in_time is None:
            check_in_time = datetime.now()
        
        today = date.today().isoformat()
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Check if attendance already marked for today
        cursor.execute('''
            SELECT id FROM attendance 
            WHERE student_id = ? AND date = ?
        ''', (student_id, today))
        
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return False  # Already marked
        
        # Mark new attendance
        cursor.execute('''
            INSERT INTO attendance (student_id, date, check_in_time, status)
            VALUES (?, ?, ?, ?)
        ''', (student_id, today, check_in_time, status))
        
        conn.commit()
        conn.close()
        return True
    
    def get_attendance_by_date(self, target_date):
        """Get attendance records for a specific date"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.name, s.roll_number, a.check_in_time, a.check_out_time, a.status
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date = ?
            ORDER BY a.check_in_time
        ''', (target_date,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_attendance_report(self, start_date, end_date):
        """Generate attendance report for date range"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.name, s.roll_number, COUNT(a.id) as total_days,
                   SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_days,
                   SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late_days
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id 
                AND a.date BETWEEN ? AND ?
            GROUP BY s.id, s.name, s.roll_number
            ORDER BY s.roll_number
        ''', (start_date, end_date))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def update_student_face_encoding(self, student_id, face_encoding_path):
        """Update face encoding path for a student"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE students SET face_encoding_path = ?
            WHERE id = ?
        ''', (face_encoding_path, student_id))
        
        conn.commit()
        conn.close()
