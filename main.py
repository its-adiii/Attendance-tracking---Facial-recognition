#!/usr/bin/env python3
"""
Face Recognition Attendance System - Main Entry Point

This is the main application entry point that provides both CLI and web interfaces
for the face recognition attendance system.

Author: Your Name
Version: 1.0.0
"""

import sys
import os
import argparse
from datetime import datetime
import configparser

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Print application banner"""
    banner = """
+------------------------------------------------------------+
|            FACE RECOGNITION ATTENDANCE SYSTEM              |
|                                                            |
|  Automated attendance tracking using advanced face         |
|  recognition technology. Register students, mark           |
|  attendance with camera, and generate reports.             |
+------------------------------------------------------------+
    """
    print(banner)

def setup_database():
    """Initialize database and create necessary directories"""
    print("Setting up database and directories...")
    
    # Create necessary directories
    directories = ['known_faces', 'captured_images', 'attendance_logs', 'templates']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"[OK] Created directory: {directory}")
    
    # Initialize database
    from database import DatabaseManager
    db = DatabaseManager()
    print("[OK] Database initialized successfully")
    
    print("Setup completed!")

def run_cli_mode():
    """Run the system in CLI mode"""
    print("\n=== CLI Mode ===")
    print("Starting command-line interface...")

    try:
        from attendance_system import AttendanceSystem
    except Exception:
        from simple_attendance import SimpleAttendanceSystem as AttendanceSystem

    system = AttendanceSystem()
    
    while True:
        print("\n" + "="*60)
        print("FACE RECOGNITION ATTENDANCE SYSTEM - CLI MODE")
        print("="*60)
        print("1. Register New Student")
        print("2. Start Attendance Session")
        print("3. View Today's Attendance")
        print("4. View All Students")
        print("5. Generate Attendance Report")
        print("6. Export Attendance to CSV")
        print("7. Manual Attendance Entry")
        print("8. System Settings")
        print("9. Exit CLI Mode")
        print("="*60)
        
        try:
            choice = input("\nEnter your choice (1-9): ").strip()
            
            if choice == '1':
                register_student_cli(system)
            elif choice == '2':
                start_attendance_cli(system)
            elif choice == '3':
                view_today_attendance_cli(system)
            elif choice == '4':
                view_students_cli(system)
            elif choice == '5':
                generate_report_cli(system)
            elif choice == '6':
                export_csv_cli(system)
            elif choice == '7':
                manual_attendance_cli(system)
            elif choice == '8':
                system_settings_cli()
            elif choice == '9':
                print("Exiting CLI mode...")
                break
            else:
                print("Invalid choice. Please enter a number between 1-9.")
                
        except KeyboardInterrupt:
            print("\n\nExiting CLI mode...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

def register_student_cli(system):
    """CLI student registration"""
    print("\n--- Register New Student ---")
    name = input("Enter student name: ").strip()
    roll_number = input("Enter roll number: ").strip()
    email = input("Enter email (optional): ").strip() or None
    
    if not name or not roll_number:
        print("Error: Name and roll number are required!")
        return
    
    print("Capturing face... Please look at the camera.")
    success, message = system.register_new_student(name, roll_number, email)
    print(f"Result: {message}")

def start_attendance_cli(system):
    """CLI attendance session"""
    print("\n--- Starting Attendance Session ---")
    print("Press 'q' to stop the session")
    
    recognized = system.start_attendance_session()
    print(f"\nSession completed. {len(recognized)} students recognized.")

def view_today_attendance_cli(system):
    """CLI view today's attendance"""
    print("\n--- Today's Attendance ---")
    attendance = system.get_today_attendance()
    
    if attendance:
        print(f"{'Name':<20} {'Roll Number':<15} {'Time':<12} {'Status':<10}")
        print("-" * 60)
        for record in attendance:
            print(f"{record[0]:<20} {record[1]:<15} {str(record[2]):<12} {record[4]:<10}")
    else:
        print("No attendance records for today.")

def view_students_cli(system):
    """CLI view all students"""
    print("\n--- All Registered Students ---")
    students = system.view_all_students()
    
    if students:
        print(f"{'ID':<5} {'Name':<20} {'Roll Number':<15} {'Email':<25} {'Face Data':<10}")
        print("-" * 80)
        for student in students:
            face_status = "Yes" if student[4] else "No"
            email = student[3] or "N/A"
            print(f"{student[0]:<5} {student[1]:<20} {student[2]:<15} {email:<25} {face_status:<10}")
    else:
        print("No students registered.")

def generate_report_cli(system):
    """CLI generate report"""
    print("\n--- Generate Attendance Report ---")
    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter end date (YYYY-MM-DD): ").strip()
    
    if not start_date or not end_date:
        print("Error: Both dates are required!")
        return
    
    report = system.generate_attendance_report(start_date, end_date)
    
    if report:
        print(f"\n{'Name':<20} {'Roll Number':<15} {'Total Days':<12} {'Present':<10} {'Late':<10}")
        print("-" * 70)
        for record in report:
            print(f"{record[0]:<20} {record[1]:<15} {record[2]:<12} {record[3]:<10} {record[4]:<10}")
    else:
        print("No records found for the given date range.")

def export_csv_cli(system):
    """CLI export to CSV"""
    print("\n--- Export Attendance to CSV ---")
    date_input = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
    
    if not date_input:
        date_input = datetime.now().date().isoformat()
    
    try:
        filename = system.export_attendance_to_csv(date_input)
        print(f"Attendance exported to: {filename}")
    except Exception as e:
        print(f"Error exporting attendance: {str(e)}")

def manual_attendance_cli(system):
    """CLI manual attendance"""
    print("\n--- Manual Attendance Entry ---")
    roll_number = input("Enter roll number: ").strip()
    status = input("Enter status (present/late/absent/excused): ").strip()
    
    if not roll_number or not status:
        print("Error: Roll number and status are required!")
        return
    
    success, message = system.manual_attendance_mark(roll_number, status)
    print(f"Result: {message}")

def system_settings_cli():
    """CLI system settings"""
    print("\n--- System Settings ---")
    print("1. View Configuration")
    print("2. Reset Database")
    print("3. Clear Face Data")
    print("4. Back to Main Menu")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == '1':
        view_configuration()
    elif choice == '2':
        reset_database()
    elif choice == '3':
        clear_face_data()
    elif choice == '4':
        return
    else:
        print("Invalid choice!")

def view_configuration():
    """View system configuration"""
    print("\n--- Current Configuration ---")
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    for section in config.sections():
        print(f"\n[{section}]")
        for key, value in config[section].items():
            print(f"{key} = {value}")

def reset_database():
    """Reset database (with confirmation)"""
    confirm = input("Are you sure you want to reset the database? (yes/no): ").strip().lower()
    if confirm == 'yes':
        try:
            os.remove('attendance.db')
            setup_database()
            print("Database reset successfully!")
        except Exception as e:
            print(f"Error resetting database: {str(e)}")
    else:
        print("Database reset cancelled.")

def clear_face_data():
    """Clear all face data"""
    confirm = input("Are you sure you want to clear all face data? (yes/no): ").strip().lower()
    if confirm == 'yes':
        try:
            import shutil
            shutil.rmtree('known_faces')
            os.makedirs('known_faces', exist_ok=True)
            print("Face data cleared successfully!")
        except Exception as e:
            print(f"Error clearing face data: {str(e)}")
    else:
        print("Face data clearing cancelled.")

def run_web_mode():
    """Run the system in web mode"""
    print("\n=== Web Mode ===")
    print("Starting web interface...")

    from web_interface import app
    
    # Load configuration
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    host = config.get('WEB_INTERFACE', 'host')
    port = config.getint('WEB_INTERFACE', 'port')
    debug = config.getboolean('WEB_INTERFACE', 'debug')
    
    print(f"Web server starting at http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    except KeyboardInterrupt:
        print("\nWeb server stopped.")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Face Recognition Attendance System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start interactive mode
  python main.py --cli              # Start CLI mode
  python main.py --web              # Start web interface
  python main.py --setup            # Setup database and directories
        """
    )
    
    parser.add_argument('--cli', action='store_true', 
                       help='Run in command-line interface mode')
    parser.add_argument('--web', action='store_true', 
                       help='Run in web interface mode')
    parser.add_argument('--setup', action='store_true', 
                       help='Setup database and directories')
    parser.add_argument('--version', action='version', version='Face Recognition Attendance System v1.0.0')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Handle setup
    if args.setup:
        setup_database()
        return
    
    # If no specific mode is chosen, show interactive menu
    if not args.cli and not args.web:
        print("\nChoose running mode:")
        print("1. Command Line Interface (CLI)")
        print("2. Web Interface")
        print("3. Setup Database")
        print("4. Exit")
        
        try:
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == '1':
                run_cli_mode()
            elif choice == '2':
                run_web_mode()
            elif choice == '3':
                setup_database()
            elif choice == '4':
                print("Goodbye!")
            else:
                print("Invalid choice!")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
        return
    
    # Run specific mode
    if args.cli:
        run_cli_mode()
    elif args.web:
        run_web_mode()

if __name__ == "__main__":
    main()
