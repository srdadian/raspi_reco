import requests
import picamera
from fort_condorcet.camera_server import StreamingServer, StreamingHandler, StreamingOutput

with picamera.PiCamera(resolution='1920x1080', framerate=24) as camera:
    camera_stream = StreamingOutput()
    # camera.rotation = 90
    camera.start_recording(camera_stream, format='mjpeg')


    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
