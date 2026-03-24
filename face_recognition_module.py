import cv2
import face_recognition
import numpy as np
import os
import pickle
import configparser
from datetime import datetime

class FaceRecognitionModule:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        self.tolerance = self.config.getfloat('FACE_RECOGNITION', 'tolerance')
        self.model = self.config.get('FACE_RECOGNITION', 'model')
        self.known_faces_dir = self.config.get('FACE_RECOGNITION', 'known_faces_dir')
        self.captured_images_dir = self.config.get('FACE_RECOGNITION', 'captured_images_dir')
        
        self.camera_index = self.config.getint('CAMERA', 'camera_index')
        self.frame_width = self.config.getint('CAMERA', 'frame_width')
        self.frame_height = self.config.getint('CAMERA', 'frame_height')
        
        # Ensure directories exist
        os.makedirs(self.known_faces_dir, exist_ok=True)
        os.makedirs(self.captured_images_dir, exist_ok=True)
        
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_roll_numbers = []
        
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load known face encodings from files"""
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_roll_numbers = []
        
        if not os.path.exists(self.known_faces_dir):
            return
        
        for filename in os.listdir(self.known_faces_dir):
            if filename.endswith('.pkl'):
                filepath = os.path.join(self.known_faces_dir, filename)
                try:
                    with open(filepath, 'rb') as f:
                        data = pickle.load(f)
                        self.known_face_encodings.append(data['encoding'])
                        self.known_face_names.append(data['name'])
                        self.known_face_roll_numbers.append(data['roll_number'])
                except Exception as e:
                    print(f"Error loading face encoding from {filename}: {e}")
    
    def save_face_encoding(self, name, roll_number, face_encoding):
        """Save face encoding to file"""
        filename = f"{roll_number}_{name.replace(' ', '_')}.pkl"
        filepath = os.path.join(self.known_faces_dir, filename)
        
        data = {
            'name': name,
            'roll_number': roll_number,
            'encoding': face_encoding
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        # Reload known faces
        self.load_known_faces()
        return filepath
    
    def capture_face_from_camera(self, capture_duration=5):
        """Capture face image from camera"""
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        
        if not cap.isOpened():
            raise Exception("Could not open camera")
        
        print("Capturing face... Look at the camera!")
        
        face_locations = []
        face_encodings = []
        captured_frame = None
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < capture_duration:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Convert BGR to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces in the frame
            face_locations = face_recognition.face_locations(rgb_frame, model=self.model)
            
            if len(face_locations) > 0:
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                captured_frame = frame.copy()
                
                # Draw rectangle around face
                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, "Face Detected!", (left, top-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.imshow('Face Capture', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        if len(face_encodings) > 0 and captured_frame is not None:
            # Save captured image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(self.captured_images_dir, f"captured_{timestamp}.jpg")
            cv2.imwrite(image_path, captured_frame)
            
            return face_encodings[0], image_path
        else:
            raise Exception("No face detected during capture")
    
    def recognize_face(self, frame):
        """Recognize faces in a frame"""
        if len(self.known_face_encodings) == 0:
            return [], [], []
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find face locations and encodings
        face_locations = face_recognition.face_locations(rgb_frame, model=self.model)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        recognized_names = []
        recognized_roll_numbers = []
        
        for face_encoding in face_encodings:
            # Compare with known faces
            matches = face_recognition.compare_faces(
                self.known_face_encodings, 
                face_encoding, 
                tolerance=self.tolerance
            )
            
            name = "Unknown"
            roll_number = "Unknown"
            
            # Find best match
            face_distances = face_recognition.face_distance(
                self.known_face_encodings, 
                face_encoding
            )
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    roll_number = self.known_face_roll_numbers[best_match_index]
            
            recognized_names.append(name)
            recognized_roll_numbers.append(roll_number)
        
        return face_locations, recognized_names, recognized_roll_numbers
    
    def start_real_time_recognition(self, attendance_callback=None):
        """Start real-time face recognition with camera"""
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        
        if not cap.isOpened():
            raise Exception("Could not open camera")
        
        print("Starting real-time face recognition. Press 'q' to quit.")
        
        recognized_students = set()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Recognize faces
            face_locations, names, roll_numbers = self.recognize_face(frame)
            
            # Draw results on frame
            for (top, right, bottom, left), name, roll_number in zip(face_locations, names, roll_numbers):
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, f"{name} ({roll_number})", (left, top-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Mark attendance if recognized and callback provided
                if name != "Unknown" and attendance_callback:
                    if roll_number not in recognized_students:
                        attendance_callback(roll_number)
                        recognized_students.add(roll_number)
            
            # Display info
            cv2.putText(frame, f"Recognized: {len(recognized_students)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Face Recognition Attendance System', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return recognized_students
    
    def get_camera_frame(self):
        """Get a single frame from camera"""
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        
        if not cap.isOpened():
            raise Exception("Could not open camera")
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise Exception("Could not capture frame")
        
        return frame
