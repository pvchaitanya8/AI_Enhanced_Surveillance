import sqlite3

# Connect to the database file (create it if it doesn't exist)
conn = sqlite3.connect('faces.db')

# Create the table if it doesn't exist
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        image_path TEXT,
        other_details TEXT
    )
''')

# Close the connection
conn.close()

##--- Adding New Profiles

def add_profile(name, image_path, other_details=""):
    conn = sqlite3.connect('faces.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO profiles (name, image_path, other_details)
        VALUES (?, ?, ?)
    ''', (name, image_path, other_details))

    conn.commit()  # Save changes to the database
    conn.close()

# # Example usage:
# add_profile("John Doe", "images/john_doe.jpg", "Employee ID: 12345")


##--- Retrieving Profiles
def get_all_profiles():
    conn = sqlite3.connect('faces.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM profiles')
    profiles = cursor.fetchall()

    conn.close()
    return profiles

# # Example usage:
# all_profiles = get_all_profiles()
# for profile in all_profiles:
#     print(profile)  # Print each profile's information


##--- Face Detection 
import face_recognition
import cv2

# Load known faces from the database
known_face_encodings = []
known_face_names = []

all_profiles = get_all_profiles()  # Retrieve profiles from the database
for profile in all_profiles:
    image = face_recognition.load_image_file(profile[2])  # Load image using path from database
    face_encoding = face_recognition.face_encodings(image)[0]  # Get encoding for the first face
    known_face_encodings.append(face_encoding)
    known_face_names.append(profile[1])  # Store corresponding name


#-- Initialize webcam
video_capture = cv2.VideoCapture(0)

while True:
    # Capture frame-by-frame
    ret, frame = video_capture.read()

    # Convert frame to RGB format (required by face_recognition)
    rgb_frame = frame[:, :, ::-1]

    # Find all faces and face encodings in the frame
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    # Loop through each face in the frame
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # See if the face is a match for any known face
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        # If a match was found, use the first one
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]

        # Draw a rectangle around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with the name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Exit the loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()
