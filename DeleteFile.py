#!/usr/bin/env python3
import re
import sys

import s3repo
from s3repo.s3repomain import *

s3repo = s3RepoMain()
logger = logger_setup.logger
logger.name = "s3repo.deleteFile"
logger.setLevel(logging.DEBUG)


def usage():
    programName = os.path.basename(sys.argv[0])
    logger.info(programName + " <username> <userpassword> file-key")


if len(sys.argv) != 4:
    programName = os.path.basename(sys.argv[0])
    logger.error("Expected 4 arguments got [" + str(len(sys.argv)) + ") - re-run program with correct arguments")
    usage()
    sys.exit(-1)

logger.info(
    "About to delete file for user with this info \n\r Username: [" + sys.argv[1] + "] \r\n password: [******]" +
    "\n\r file-key: [" + sys.argv[3] + "]")

s3repo.deleteFile(bucket_name=sys.argv[1], user_password=sys.argv[2], user_Key=sys.argv[3])
