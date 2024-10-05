import os
import time
import psutil
import signal
import requests
import traceback
from multiprocessing import Process, Queue

from fort_condorcet.camera_server import StreamingServer, StreamingHandler, StreamingOutput
from fort_condorcet.face_regognition_process import face_recognition_process
from fort_condorcet.http_server_process import http_server

global_kill_flag = True


def child_exited(sig, frame):
    global global_kill_flag
    if global_kill_flag:
        global_kill_flag = False  # So no recursive call on the children processes.
        pid = os.getpid()
        parent = psutil.Process(pid)
        traceback.print_stack(frame)
        print('Received signal {} on line {} in {}'.format(
            str(sig), str(frame.f_lineno), frame.f_code.co_filename))
        for child in parent.children(recursive=False):
            print('Terminating child process {}'.format(child))
            child.terminate()
        parent.terminate()


def main_process():
    img_q = Queue()

    signal.signal(signal.SIGCHLD, child_exited)

    # Face reco process
    face_recognition_p = Process(target=face_recognition_process,
                                 args=(img_q, False,))
    face_recognition_p.start()

    # http server
    http_server_p = Process(target=http_server,
                            args=(img_q, 'localhost', 8000))
    http_server_p.start()

    time.sleep(60)  # Just long enough for the feed server to do something.


if __name__ == '__main__':
    main_process()
