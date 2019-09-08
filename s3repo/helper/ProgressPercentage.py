import os
import sys
import threading

"""
This code has been borrowed from : https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html
"""


class ProgressPercentage(object):

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify, assume this is hooked up to a single filename
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\rUploading: %s  %s / %s  (%.2f%%)" % (
                    self._filename, (self._seen_so_far / 1000000), (self._size / 1000000),
                    percentage))
            sys.stdout.flush()
