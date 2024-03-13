import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
from pymongo import MongoClient
import face_recognition
import cv2
import geocoder
import webbrowser
import datetime
from PIL import Image

# Connecting to MongoDB
client = MongoClient('mongodb://localhost:27017')    #Change This MongoClient 
db = client['face_recognition']
collection = db['known_faces']
found_collection = db['found']

# Finding current location of camera
g = geocoder.ip('me')
location_cam = f"{g.latlng[0]:.6f}°N {g.latlng[1]:.6f}°E"

# Function to add a person to the database
def add_person_window():
    add_window = tk.Toplevel(root)
    add_window.title("Add a Person")
    add_window.config(bg="#1E1E1E")

    label_fg = "#FFFFFF"
    entry_bg = "#303030"
    entry_fg = "#FFFFFF"
    text_bg = "#303030"
    text_fg = "#FFFFFF"
    button_bg = "#006400"
    button_fg = "#FFFFFF"

    name_label = tk.Label(add_window, text="Name:", bg="#1E1E1E", fg=label_fg)
    name_label.grid(row=0, column=0, padx=10, pady=5)

    name_entry = tk.Entry(add_window, bg=entry_bg, fg=entry_fg)
    name_entry.grid(row=0, column=1, padx=10, pady=5)

    mobile_label = tk.Label(add_window, text="Mobile Number:", bg="#1E1E1E", fg=label_fg)
    mobile_label.grid(row=1, column=0, padx=10, pady=5)

    mobile_entry = tk.Entry(add_window, bg=entry_bg, fg=entry_fg)
    mobile_entry.grid(row=1, column=1, padx=10, pady=5)

    other_details_label = tk.Label(add_window, text="Other Details:", bg="#1E1E1E", fg=label_fg)
    other_details_label.grid(row=2, column=0, padx=10, pady=5)

    other_details_text = tk.Text(add_window, height=8, width=40, bg=text_bg, fg=text_fg)
    other_details_text.grid(row=2, column=1, padx=10, pady=5, rowspan=2)

    add_button = tk.Button(add_window, text="Add", bg=button_bg, fg=button_fg, command=lambda: add_person(name_entry.get(), mobile_entry.get(), other_details_text.get("1.0", tk.END).strip(), add_window))
    add_button.grid(row=4, columnspan=2, padx=10, pady=5)

def add_person(name, mobile_number, other_details, add_window):
    if name and mobile_number:
        if not mobile_number.isdigit():
            status_label.config(text="Mobile number must contain only numbers.")
            return

        image_path = filedialog.askopenfilename()

        if image_path:
            encoding = face_recognition.face_encodings(face_recognition.load_image_file(image_path))[0]
            encoding_list = encoding.tolist()

            collection.insert_one({'name': name, 'mobile_number': mobile_number, 'other_details': other_details, 'image_path': image_path, 'encoding': encoding_list})
            status_label.config(text="Person added successfully!")
            add_window.destroy()
        else:
            status_label.config(text="Please select an image.")
    else:
        status_label.config(text="Please provide both name and mobile number.")

def alert(person_name):
    person = collection.find_one({'name': person_name})
    if person:
        message = f"{person_name} is at location {location_cam} during {datetime.datetime.now()}"
        number_str = str(person['mobile_number'])
        url = "https://wa.me/+91" + number_str + "?text=" + message
        webbrowser.open(url)

    else:
        print("Person not found in database.")

# Function to start searching from the webcam or a video file
def start_search(video_path=None, frame_skip=1):
    def recognize_faces():
        if video_path:
            video_capture = cv2.VideoCapture(video_path)
        else:
            video_capture = cv2.VideoCapture(0)

        notification_window = tk.Toplevel(root)
        notification_window.title("Notifications")
        notification_window.configure(bg="#222")
        notification_frame = tk.Frame(notification_window, bg="#000")
        notification_frame.pack(padx=100, pady=30)

        while True:
            ret, frame = video_capture.read()

            if not ret:
                break

            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = {}
                for person in collection.find():
                    matches[person['name']] = face_recognition.compare_faces([person['encoding']], face_encoding)[0]

                names = []

                for key, value in matches.items():
                    if value:
                        names.append(key)

                if names:
                    for name in names:
                        found_collection.insert_one({'name': name, 'timestamp': datetime.datetime.now(), 'location_cam': location_cam})
                        alert_button = tk.Button(notification_frame, text=f"Alert, Found:      {name}", command=lambda n=name: alert(n))
                        alert_button.pack(pady=5)

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, ", ".join(names) if names else "Unknown", (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

            cv2.imshow('Real Time Face Recognition', frame)

            # Waiting for 'q' key to exit the loop
            if cv2.waitKey(1) == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

    recognize_faces()

def start_search_from_file():
    video_path = filedialog.askopenfilename()
    if video_path:
        start_search(video_path)

def resize_background(event):
    global background_photo
    width = event.width
    height = event.height
    resized_image = background_image.resize((width, height), Image.ANTIALIAS if hasattr(Image, 'ANTIALIAS') else Image.LANCZOS)
    background_photo = ImageTk.PhotoImage(resized_image)
    background_label.config(image=background_photo)

root = tk.Tk()
root.title("AI Enhanced Surveillance")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

reduced_width = screen_width - 100
reduced_height = screen_height - 100

root.geometry(f"{reduced_width}x{reduced_height}")

background_image = Image.open("Background.png")
background_photo = ImageTk.PhotoImage(background_image)

background_label = tk.Label(root, image=background_photo)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

root.bind("<Configure>", resize_background)

button_style = ttk.Style()
button_style.configure("Rounded.TButton", foreground="black", background="green", font=('Helvetica', 14, 'bold'), padding=10, borderwidth=15, relief="groove")

add_button = ttk.Button(root, text="Add a Person", style="Rounded.TButton", command=add_person_window)
add_button.place(relx=0.5, rely=0.4, anchor="center")

status_label = tk.Label(root, text="")
status_label.place(relx=0.5, rely=0.5, anchor="center")

start_button_file = ttk.Button(root, text="Start Searching from Video File", style="Rounded.TButton", command=start_search_from_file)
start_button_file.place(relx=0.5, rely=0.6, anchor="center")

start_button_webcam = ttk.Button(root, text="Start Searching from Webcam", style="Rounded.TButton", command=start_search)
start_button_webcam.place(relx=0.5, rely=0.7, anchor="center")

root.mainloop()
