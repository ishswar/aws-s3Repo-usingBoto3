#!/usr/bin/env python3
import re
import sys

import s3repo
from s3repo.s3repomain import *

s3repo = s3RepoMain()
logger = logger_setup.logger
logger.name = "s3repo.getFile"
logger.setLevel(logging.DEBUG)


def usage():
    programName = os.path.basename(sys.argv[0])
    logger.info(programName + " <username> <userpassword> file-key path-to-save-file-to")


if len(sys.argv) != 5:
    programName = os.path.basename(sys.argv[0])
    logger.error("Expected 5 arguments got [" + str(len(sys.argv)) + ") - re-run program with correct arguments")
    usage()
    sys.exit(-1)

logger.info(
    "About to get file for user with this info \n\r Username: [" + sys.argv[1] + "] \r\n password: [******]" +
    "\n\r file-key: [" + sys.argv[3] + "] \r\n output location: [" + sys.argv[4] + "]")

s3repo.getFile(bucket_name=sys.argv[1], user_password=sys.argv[2], user_Key=sys.argv[3], output_location=sys.argv[4])
