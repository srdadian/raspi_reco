class AbstractCamera:
    def __init__(self, default_camera=0):
        self.default_camera = default_camera

    def capture(self):
        print("Not implemented")

    def release(self):
        print("Not implemented")
