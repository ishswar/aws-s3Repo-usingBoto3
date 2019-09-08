#!/usr/bin/env python3
import os
import re
import sys

import s3repo
from s3repo.helper import logger_setup
from s3repo.s3repomain import s3RepoMain

"""
This is a 
"""
s3repo = s3RepoMain()
logger = logger_setup.logger
logger.name = "s3repo.createUser"


def usage():
    programName = os.path.basename(sys.argv[0])
    logger.info(programName + " <username> <userpassword> <usersEmail>")


if len(sys.argv) != 4:
    programName = os.path.basename(sys.argv[0])
    logger.error("Expected 4 arguments got [" + str(len(sys.argv)) + ") - re-run program with correct arguments")
    usage()
    sys.exit(-1)

if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", sys.argv[3]):
    logger.error("Email address provided for user is not valid [" + sys.argv[3] + "]")
    sys.exit(-1)

s3repo.logger.info(
    "About to create user with this info \n\r Username: [" + sys.argv[1] + "] \r\n password: [******] \r\n E-mail "
                                                                           "address: [" + sys.argv[3] + "]")

s3repo.create_user(user_name=sys.argv[1], password=sys.argv[2], email_id=sys.argv[3])
