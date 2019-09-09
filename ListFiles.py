#!/usr/bin/env python3
import re
import sys

import s3repo
from s3repo.s3repomain import *

s3repo = s3RepoMain()
logger = logger_setup.logger
logger.name = "s3repo.listFiles"
logger.setLevel(logging.DEBUG)


def usage():
    programName = os.path.basename(sys.argv[0])
    logger.info(programName + " <username> <userpassword>")


if len(sys.argv) != 3:
    programName = os.path.basename(sys.argv[0])
    logger.error("Expected 3 arguments got [" + str(len(sys.argv)) + ") - re-run program with correct arguments")
    usage()
    sys.exit(-1)

logger.info(
    "About to list files for user with this info \n\r Username: [" + sys.argv[1] + "] \r\n password: [******]")

s3repo.listFiles(bucket_name=sys.argv[1], user_password=sys.argv[2])
