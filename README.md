# Face Recognition Attendance System

An automated attendance tracking system using advanced face recognition technology. This system allows you to register students, mark attendance using camera-based face recognition, and generate comprehensive reports.

## Features

- **Face Recognition**: Automatic student identification using advanced face recognition algorithms
- **Student Registration**: Easy student registration with face capture
- **Real-time Attendance**: Mark attendance automatically using camera
- **Manual Entry**: Backup manual attendance entry option
- **Web Interface**: Modern, responsive web interface for easy management
- **CLI Mode**: Command-line interface for server administration
- **Reports**: Generate detailed attendance reports with date ranges
- **Export**: Export attendance data to CSV format
- **Dashboard**: Real-time statistics and attendance overview
- **Database**: SQLite database for reliable data storage

## Installation

### Prerequisites

- Python 3.7 or higher
- Camera (webcam) for face recognition
- Windows, macOS, or Linux operating system

### Setup Steps

1. **Clone or Download** the project files to your local machine

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Database**:
   ```bash
   python main.py --setup
   ```

4. **Run the Application**:
   ```bash
   python main.py
   ```

## Usage

### Interactive Mode

Simply run `python main.py` and choose from the menu:
- Command Line Interface (CLI)
- Web Interface
- Setup Database

### Web Interface

Start the web server:
```bash
python main.py --web
```

Then open your browser and navigate to `http://127.0.0.1:5000`

### CLI Mode

For command-line operation:
```bash
python main.py --cli
```

## Getting Started

### 1. Register Students

1. Open the web interface or CLI
2. Navigate to "Register Student"
3. Enter student details (name, roll number, email)
4. Capture face using camera when prompted
5. Student is now registered and ready for attendance

### 2. Mark Attendance

**Automatic (Face Recognition)**:
1. Go to "Mark Attendance" section
2. Click "Start Attendance Session"
3. Students look at the camera
4. System automatically recognizes and marks attendance
5. Click "Stop Session" when done

**Manual Entry**:
1. Go to "Manual Attendance" section
2. Enter roll number and status
3. Click "Mark Attendance"

### 3. View Reports

1. Navigate to "Reports" section
2. Select date range
3. Choose report type
4. Generate and view/export reports

## Configuration

The system uses `config.ini` for configuration:

```ini
[DATABASE]
db_file = attendance.db

[FACE_RECOGNITION]
tolerance = 0.6
model = hog
known_faces_dir = known_faces
captured_images_dir = captured_images

[ATTENDANCE]
late_threshold = 09:00
auto_save_interval = 30

[WEB_INTERFACE]
host = 127.0.0.1
port = 5000
debug = True

[CAMERA]
camera_index = 0
frame_width = 640
frame_height = 480
```

### Key Settings

- **tolerance**: Face recognition sensitivity (0.4-0.8 recommended)
- **late_threshold**: Time after which students are marked as late
- **camera_index**: Camera device number (0 for default camera)

## Project Structure

```
Facial tracking/
├── main.py                 # Main application entry point
├── attendance_system.py    # Core attendance logic
├── face_recognition_module.py  # Face recognition functionality
├── database.py            # Database management
├── web_interface.py       # Flask web application
├── config.ini             # Configuration file
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   ├── register.html
│   ├── attendance.html
│   ├── view_attendance.html
│   ├── students.html
│   ├── reports.html
│   ├── manual_attendance.html
│   └── edit_student.html
├── known_faces/           # Stored face encodings
├── captured_images/       # Captured face images
├── attendance_logs/       # Attendance log files
└── attendance.db          # SQLite database
```

## API Endpoints

The web interface provides the following API endpoints:

- `GET /` - Home page
- `GET /register` - Student registration page
- `POST /register_student` - Register new student
- `GET /attendance` - Attendance marking page
- `GET /view_attendance` - View attendance records
- `GET /students` - Manage students
- `GET /reports` - Generate reports
- `GET /api/camera_feed` - Live camera feed
- `POST /api/recognize_face` - Face recognition API

## Troubleshooting

### Common Issues

1. **Camera not detected**:
   - Check camera connection
   - Verify camera_index in config.ini
   - Try different camera index values (0, 1, 2...)

2. **Face recognition not working**:
   - Ensure good lighting conditions
   - Check if face data is properly registered
   - Adjust tolerance value in config.ini

3. **Database errors**:
   - Run `python main.py --setup` to reinitialize
   - Check file permissions for database directory

4. **Web interface not accessible**:
   - Check if port 5000 is available
   - Verify firewall settings
   - Try different port in config.ini

### Performance Tips

- Use good lighting for face recognition
- Position camera at eye level
- Ensure students face the camera directly
- Regular backup of attendance.db file

## Security Considerations

- Store attendance.db in secure location
- Regular backups of face data and database
- Limit access to web interface in production
- Use HTTPS in production environment

## Dependencies

- **OpenCV** (opencv-python): Camera and image processing
- **face-recognition**: Face recognition algorithms
- **Flask**: Web framework
- **NumPy**: Numerical computations
- **Pillow**: Image handling
- **configparser**: Configuration management

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Verify all dependencies are installed
3. Ensure camera is working properly
4. Review configuration settings

## Version History

- **v1.0.0**: Initial release with core features
  - Face recognition attendance
  - Web interface
  - CLI mode
  - Report generation
  - CSV export functionality

---

**Note**: This system is designed for educational and organizational use. Ensure compliance with local privacy laws and regulations when implementing biometric attendance systems.
