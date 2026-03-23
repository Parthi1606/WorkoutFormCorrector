"""
Pose Utilities 
"""

import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe components
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def calculate_angle(a, b, c):
    """
    Calculate angle between three points
    a, b, c are (x, y) coordinates
    Angle at point b
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    # Calculate vectors
    ba = a - b
    bc = c - b
    
    # Calculate angle in radians
    angle_rad = np.arctan2(np.linalg.det([ba, bc]), np.dot(ba, bc))
    
    # Convert to degrees
    angle_deg = np.degrees(angle_rad)
    
    # Make sure angle is positive
    if angle_deg < 0:
        angle_deg = 360 + angle_deg
    
    return angle_deg

def get_landmark_coords(landmarks, idx, frame_shape):
    """
    Get x, y coordinates of a landmark
    idx: MediaPipe landmark index
    frame_shape: (height, width, channels)
    """
    if landmarks and idx < len(landmarks.landmark):
        h, w = frame_shape[:2]
        x = int(landmarks.landmark[idx].x * w)
        y = int(landmarks.landmark[idx].y * h)
        return (x, y)
    return None

def draw_angle(frame, point, angle, color=(0, 255, 0)):
    """
    Draw angle text on frame
    """
    cv2.putText(frame, f"{int(angle)}°", 
                (point[0] + 10, point[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

def draw_feedback(frame, feedback_list, position=(10, 30)):
    """
    Draw feedback messages
    """
    y_offset = position[1]
    for i, msg in enumerate(feedback_list[:6]):  # Show up to 6 messages
        # Color based on message content
        if "✅" in msg or "Good" in msg or "✓" in msg:
            color = (0, 255, 0)  # Green
        elif "⚠️" in msg or "❌" in msg:
            color = (0, 0, 255)  # Red
        else:
            color = (0, 255, 255)  # Yellow
        
        cv2.putText(frame, msg, (position[0], y_offset + i * 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

def draw_skeleton(frame, landmarks, connections, color=(0, 255, 0), thickness=2):
    """
    Draw skeleton connections between landmarks
    """
    h, w = frame.shape[:2]
    points = []
    
    # Draw all landmark points
    for i in range(len(landmarks.landmark)):
        x = int(landmarks.landmark[i].x * w)
        y = int(landmarks.landmark[i].y * h)
        points.append((x, y))
        # Draw small circles at each landmark
        cv2.circle(frame, (x, y), 4, color, -1)
    
    # Draw connections
    for connection in connections:
        start_idx, end_idx = connection
        if start_idx < len(points) and end_idx < len(points):
            cv2.line(frame, points[start_idx], points[end_idx], color, thickness)
    
    return frame