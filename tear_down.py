#!/usr/bin/env python3
import re
import sys
from getpass import getpass

import s3repo
from s3repo.s3repomain import *

s3repo = s3RepoMain()
logger = logger_setup.logger
logger.name = "s3repo.tearDownAll"


def yes_or_no(question):
    while "the answer is invalid":
        reply = str(input(question + ' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False


logger.info(
    "About to start tear down of Repo")

if yes_or_no("Delete all users and their repos ? "):
    input_admin_password = getpass("Enter admin password: ")
    s3repo.tear_down_all(input_admin_password)
