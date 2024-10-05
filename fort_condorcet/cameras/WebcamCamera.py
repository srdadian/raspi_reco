import cv2

from fort_condorcet.cameras.AbstractCamera import AbstractCamera


class WebcamCamera(AbstractCamera):
    def __init__(self, default_camera=0):
        super().__init__(default_camera)
        self.video_capture = cv2.VideoCapture(default_camera)

    def capture(self):
        ret, frame = self.video_capture.read()
        return frame

    def release(self):
        self.video_capture.release()
        cv2.destroyAllWindows()
