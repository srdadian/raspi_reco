import io
import logging
import socketserver
from http import server
from queue import Empty
from threading import Condition

import cv2

from fort_condorcet.cameras.RaspiCamera import RaspiCamera
from fort_condorcet.cameras.WebcamCamera import WebcamCamera

PAGE = open('public/page.html').read()


def display_faces(face_locations, face_names, frame):
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def http_server(faces_q, host, port, raspi=False):
    print('Starting http server')
    camera = RaspiCamera() if raspi else WebcamCamera(default_camera=1)

    class StreamingHandler(server.BaseHTTPRequestHandler):
        face_locations, face_names = [], []

        def do_GET(self):
            if self.path == '/':
                self.send_response(301)
                self.send_header('Location', '/index.html')
                self.end_headers()
            elif self.path == '/index.html':
                content = PAGE.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)
            elif self.path == '/stream.mjpg':
                self.send_response(200)
                self.send_header('Age', 0)
                self.send_header('Cache-Control', 'no-cache, private')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
                self.end_headers()
                try:
                    while True:
                        try:
                            frame = camera.capture()
                            if not faces_q.empty():
                                self.face_locations, self.face_names = faces_q.get()
                            display_faces(self.face_locations, self.face_names, frame)
                            _, jpeg_data = cv2.imencode('.jpg', frame)  # Convert to jpg
                            jpeg_bytes = jpeg_data.tobytes()
                            # with output.condition:
                            #     output.condition.wait()
                            #     frame = output.frame
                            self.wfile.write(b'--FRAME\r\n')
                            self.send_header('Content-Type', 'image/jpeg')
                            self.send_header('Content-Length', len(jpeg_bytes))
                            self.end_headers()
                            self.wfile.write(jpeg_bytes)
                            self.wfile.write(b'\r\n')
                        except Empty:
                            # msg = None
                            pass
                except Exception as e:
                    logging.warning(
                        'Removed streaming client %s: %s',
                        self.client_address, str(e))
            else:
                self.send_error(404)
                self.end_headers()

    server_address = (host, int(port))
    httpd = StreamingServer(server_address, StreamingHandler, bind_and_activate=False)
    httpd.allow_reuse_address = True
    httpd.daemon_threads = True

    httpd.server_bind()
    httpd.server_activate()
    httpd.serve_forever()
