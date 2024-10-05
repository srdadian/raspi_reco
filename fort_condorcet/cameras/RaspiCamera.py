import numpy as np

import cv2

from fort_condorcet.cameras.AbstractCamera import AbstractCamera


class RaspiCamera(AbstractCamera):
    def __init__(self, default_camera=0):
        import picamera
        super().__init__(default_camera)
        self.camera = picamera.PiCamera()
        self.camera.resolution = (320, 240)
        self.img_output = np.empty((240, 320, 3), dtype=np.uint8)

    def capture(self):
        self.camera.capture(self.img_output, format="rgb")
        return self.img_output

    def release(self):
        self.camera.stop_recording()
        cv2.destroyAllWindows()
