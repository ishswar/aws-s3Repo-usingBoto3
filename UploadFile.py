#!/usr/bin/env python3
import re
import sys

import s3repo
from s3repo.s3repomain import *

s3repo = s3RepoMain()
logger = logger_setup.logger
logger.name = "s3repo.uploadFile"

def usage():
    programName = os.path.basename(sys.argv[0])
    logger.info(programName + " <username> <userpassword> <user-key> <file-path-to-upload>")


if len(sys.argv) != 5:
    programName = os.path.basename(sys.argv[0])
    logger.error("Expected 5 arguments got [" + str(len(sys.argv)) + ") - re-run program with correct arguments")
    usage()
    sys.exit(-1)

logger.info(
    "About to upload file for user with this info \n\r Username: [" + sys.argv[1] + "] \r\n password: [******] \r\n "
                                                                                    "user-key: "+sys.argv[3]+"")

s3repo.uploadFile(user_name=sys.argv[1],user_password=sys.argv[2],file_key=sys.argv[3],file=sys.argv[4])


# print('Argument List:', str(sys.argv))
