import requests
import picamera
from fort_condorcet.camera_server import StreamingServer, StreamingHandler, StreamingOutput

with picamera.PiCamera(resolution='1920x1080', framerate=24) as camera:
    output = StreamingOutput()
    # Uncomment the next line to change your Pi's Camera rotation (in degrees)
    # camera.rotation = 90
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
