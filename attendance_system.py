import os
import cv2
import sqlite3
from datetime import datetime, time
import configparser
from database import DatabaseManager
from face_recognition_module import FaceRecognitionModule

class AttendanceSystem:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        self.db_manager = DatabaseManager(config_file)
        self.face_recognition = FaceRecognitionModule(config_file)
        
        self.late_threshold = self.config.get('ATTENDANCE', 'late_threshold')
        self.auto_save_interval = self.config.getint('ATTENDANCE', 'auto_save_interval')
        
        # Parse late threshold time
        hour, minute = map(int, self.late_threshold.split(':'))
        self.late_time = time(hour, minute)
    
    def register_new_student(self, name, roll_number, email=None):
        """Register a new student with face recognition"""
        # Check if student already exists
        existing = self.db_manager.get_student_by_roll(roll_number)
        if existing:
            return False, "Student with this roll number already exists"
        
        try:
            print(f"Registering new student: {name} ({roll_number})")
            print("Please look at the camera for face capture...")
            
            # Capture face encoding
            face_encoding, image_path = self.face_recognition.capture_face_from_camera()
            
            # Save face encoding
            encoding_path = self.face_recognition.save_face_encoding(name, roll_number, face_encoding)
            
            # Add to database
            student_id = self.db_manager.add_student(name, roll_number, email, encoding_path)
            
            if student_id:
                return True, f"Student {name} registered successfully!"
            else:
                return False, "Failed to register student in database"
                
        except Exception as e:
            return False, f"Error during registration: {str(e)}"
    
    def mark_attendance_callback(self, roll_number):
        """Callback function for marking attendance during real-time recognition"""
        student = self.db_manager.get_student_by_roll(roll_number)
        if student:
            student_id = student[0]
            current_time = datetime.now()
            
            # Determine if late
            status = 'late' if current_time.time() > self.late_time else 'present'
            
            # Mark attendance
            success = self.db_manager.mark_attendance(student_id, current_time, status)
            
            if success:
                print(f"✓ Attendance marked for {student[1]} ({roll_number}) - {status}")
            else:
                print(f"✗ Attendance already marked for {student[1]} ({roll_number})")
    
    def start_attendance_session(self):
        """Start an attendance marking session"""
        print("Starting attendance session...")
        print("Press 'q' to stop the session")
        
        recognized_students = self.face_recognition.start_real_time_recognition(
            self.mark_attendance_callback
        )
        
        print(f"\nSession completed. Total students recognized: {len(recognized_students)}")
        return recognized_students
    
    def get_today_attendance(self):
        """Get today's attendance records"""
        today = datetime.now().date().isoformat()
        return self.db_manager.get_attendance_by_date(today)
    
    def generate_attendance_report(self, start_date, end_date):
        """Generate attendance report for date range"""
        return self.db_manager.get_attendance_report(start_date, end_date)
    
    def view_all_students(self):
        """View all registered students"""
        return self.db_manager.get_all_students()
    
    def export_attendance_to_csv(self, date, filename=None):
        """Export attendance for a specific date to CSV"""
        if filename is None:
            filename = f"attendance_{date}.csv"
        
        attendance_data = self.db_manager.get_attendance_by_date(date)
        
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Name', 'Roll Number', 'Check In Time', 'Check Out Time', 'Status'])
            
            for row in attendance_data:
                writer.writerow([
                    row[0],  # Name
                    row[1],  # Roll Number
                    row[2],  # Check In Time
                    row[3],  # Check Out Time
                    row[4]   # Status
                ])
        
        return filename
    
    def delete_student(self, roll_number):
        """Delete a student from the system"""
        conn = sqlite3.connect(self.db_manager.db_file)
        cursor = conn.cursor()
        
        # Get student info first to delete face encoding file
        student = self.db_manager.get_student_by_roll(roll_number)
        if student:
            face_encoding_path = student[4]
            if face_encoding_path and os.path.exists(face_encoding_path):
                os.remove(face_encoding_path)
        
        # Delete from database
        cursor.execute('DELETE FROM students WHERE roll_number = ?', (roll_number,))
        conn.commit()
        conn.close()
        
        # Reload known faces
        self.face_recognition.load_known_faces()
        
        return True
    
    def update_student_info(self, roll_number, new_name=None, new_email=None):
        """Update student information"""
        conn = sqlite3.connect(self.db_manager.db_file)
        cursor = conn.cursor()
        
        if new_name:
            cursor.execute('UPDATE students SET name = ? WHERE roll_number = ?', 
                          (new_name, roll_number))
        if new_email:
            cursor.execute('UPDATE students SET email = ? WHERE roll_number = ?', 
                          (new_email, roll_number))
        
        conn.commit()
        conn.close()
        
        # Update face recognition data
        self.face_recognition.load_known_faces()
        
        return True
    
    def manual_attendance_mark(self, roll_number, status='present'):
        """Manually mark attendance for a student"""
        student = self.db_manager.get_student_by_roll(roll_number)
        if not student:
            return False, "Student not found"
        
        student_id = student[0]
        current_time = datetime.now()
        
        success = self.db_manager.mark_attendance(student_id, current_time, status)
        
        if success:
            return True, f"Attendance marked for {student[1]}"
        else:
            return False, "Attendance already marked for today"

# CLI Interface for testing
def main():
    system = AttendanceSystem()
    
    while True:
        print("\n=== Face Recognition Attendance System ===")
        print("1. Register New Student")
        print("2. Start Attendance Session")
        print("3. View Today's Attendance")
        print("4. View All Students")
        print("5. Generate Attendance Report")
        print("6. Export Attendance to CSV")
        print("7. Exit")
        
        choice = input("Enter your choice (1-7): ")
        
        if choice == '1':
            name = input("Enter student name: ")
            roll_number = input("Enter roll number: ")
            email = input("Enter email (optional): ") or None
            
            success, message = system.register_new_student(name, roll_number, email)
            print(message)
        
        elif choice == '2':
            system.start_attendance_session()
        
        elif choice == '3':
            attendance = system.get_today_attendance()
            if attendance:
                print("\nToday's Attendance:")
                for record in attendance:
                    print(f"{record[0]} ({record[1]}) - {record[2]} - {record[4]}")
            else:
                print("No attendance records for today")
        
        elif choice == '4':
            students = system.view_all_students()
            if students:
                print("\nAll Registered Students:")
                for student in students:
                    print(f"{student[1]} ({student[2]}) - {student[3] or 'No email'}")
            else:
                print("No students registered")
        
        elif choice == '5':
            start_date = input("Enter start date (YYYY-MM-DD): ")
            end_date = input("Enter end date (YYYY-MM-DD): ")
            
            report = system.generate_attendance_report(start_date, end_date)
            if report:
                print("\nAttendance Report:")
                print("Name | Roll Number | Total Days | Present | Late")
                for record in report:
                    print(f"{record[0]} | {record[1]} | {record[2]} | {record[3]} | {record[4]}")
            else:
                print("No records found for the given date range")
        
        elif choice == '6':
            date = input("Enter date (YYYY-MM-DD) or press Enter for today: ")
            if not date:
                date = datetime.now().date().isoformat()
            
            filename = system.export_attendance_to_csv(date)
            print(f"Attendance exported to {filename}")
        
        elif choice == '7':
            print("Exiting system...")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()