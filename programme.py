import os
import cv2
import face_recognition
import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import ssl
import smtplib
from email.message import EmailMessage
import shutil
import time

class FaceDetectionHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".jpg"):
            process_image(event.src_path)

def process_image(image_path):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    for i, face_encoding in enumerate(face_encodings):
        face_name = "Unknown"
        matches = face_recognition.compare_faces(known_faces, face_encoding)
        if True in matches:
            index = matches.index(True)
            face_name = known_names[index]

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        face_file_name = f"{face_name}_{current_time}_{i}.jpg"
        face_file_path = os.path.join("faces", face_file_name)
        cv2.imwrite(face_file_path, image[face_locations[i][0]:face_locations[i][2], face_locations[i][3]:face_locations[i][1]])

        # Save face name and timestamp to "faces.txt"
        with open("faces.txt", "a") as file:
            file.write(f"{face_name}\t{current_time}\n")

        send_email(face_file_path, face_name)

def send_email(attachment_path, face_name):
    email_sender = 'ettmustapha1@gmail.com'
    email_password = 'beyotnushvxbtrlt'
    email_receiver = 'omargary03@gmail.com'

    if face_name == "Unknown":
        subject = 'Unknown Face Detected'
        body = 'An unknown face has been detected.'
    else:
        subject = f'New face detected: {face_name}'
        body = f'A new face ({face_name}) has been detected.'

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    with open(attachment_path, 'rb') as f:
        attachment_data = f.read()
        attachment_name = os.path.basename(attachment_path)
        em.add_attachment(attachment_data, maintype='image', subtype='jpeg', filename=attachment_name)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.send_message(em)

def move_new_photos(source_dir, destination_dir):
    # Create the destination folder if it doesn't exist
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Dictionary to store existing files
    existing_files = {}

    while True:
        # Search for new files
        for file_name in os.listdir(source_dir):
            file_path = os.path.join(source_dir, file_name)
            if os.path.isfile(file_path) and file_name not in existing_files:
                existing_files[file_name] = file_path
                if file_name.endswith(".jpg"):
                    destination_path = os.path.join(destination_dir, file_name)
                    shutil.move(file_path, destination_path)
                    print(f"Photo {file_name} moved to {destination_dir}")
                    process_image(destination_path)

        time.sleep(1)  # Wait for 1 second before the next check

if __name__ == "__main__":
    # Load known faces from the "database" folder
    database_dir = "database"
    database = [f for f in os.listdir(database_dir) if os.path.isfile(os.path.join(database_dir, f))]
    known_faces = []
    known_names = []
    for image_name in database:
        image_path = os.path.join(database_dir, image_name)
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        if len(face_encodings) > 0:
            known_faces.append(face_encodings[0])
            name = image_name.split(".")[0]
            known_names.append(name)

    # Create the "faces" folder if it doesn't exist
    os.makedirs("faces", exist_ok=True)

    # Move files from the shared folder to the destination folder
    source_directory = r"\\172.16.8.1\Camera1\2023-06-20"  # Path to the source folder
    destination_directory = r"C:\Users\HP Pro\Desktop\reconnaissance faciale par image automatisée\images"  # Path to the destination folder
    move_new_photos(source_directory, destination_directory)

    # Monitor the "images" folder for new files
    images_dir = "images"
    event_handler = FaceDetectionHandler()
    observer = Observer()
    observer.schedule(event_handler, images_dir, recursive=False)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
