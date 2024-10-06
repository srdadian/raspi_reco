import os
import time
import numpy as np

import cv2
import face_recognition

from fort_condorcet.cameras.RaspiCamera import RaspiCamera
from fort_condorcet.cameras.WebcamCamera import WebcamCamera


def load_known_persons(directory):
    known_face_encodings, known_names = list(), list()
    for img in os.listdir(directory):
        img_path = os.path.join(directory, img)
        person = face_recognition.load_image_file(img_path)
        person_name = img.split(".")[0]
        face_encoding = face_recognition.face_encodings(person)[0]
        known_names.append(person_name)
        known_face_encodings.append(face_encoding)
    return known_names, known_face_encodings


def face_recognition_process(image_q, raspi=False):
    print("Started face reco pricess")
    camera = RaspiCamera() if raspi else WebcamCamera(default_camera=1)
    known_face_names, known_face_encodings = load_known_persons('images')

    while True:
        frame = camera.capture()  # Get a video frame

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]
        rgb_small_frame = cv2.cvtColor(rgb_small_frame, cv2.COLOR_BGR2RGB)

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # # If a match was found in known_face_encodings, just use the first one.
            # if True in matches:
            #     first_match_index = matches.index(True)
            #     name = known_face_names[first_match_index]

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_face_encodings,
                                                            face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            face_names.append(name)

            if face_names:
                image_q.put((face_locations, face_names))
                time.sleep(1)

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
