import json
import sys
from pathlib import Path

import boto3
import botocore
from botocore.exceptions import NoRegionError, NoCredentialsError
from botocore.exceptions import ClientError


class awsHelper:

    def __init__(self, region_name, profile="default"):
        print('Python version: ' + sys.version)
        print('Boto3 version: ' + boto3.__version__)
        self.region_name = region_name
        self.profile = profile

    def get_aws_connection(self):
        try:
            session = self.getsession(self.region_name)
            s3 = session.resource('s3')
            for bucket in s3.buckets.all():
                break;

            print("Connection to AWS was successful");
            return session

        except (NoRegionError, NoCredentialsError) as e:
            print("Error connecting to AWS: " + str(e))
            msg = "The AWS CLI is not configured."
            msg += " Please configure it using instructions at"
            msg += " http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html"
            print(msg);
            sys.exit()

    def getsession(self, region_name=None):
        session = botocore.session.Session(profile=self.profile)
        try:
            session3 = boto3.session.Session(region_name=region_name, profile_name=self.profile)
            # print(session3.region_name)
        except botocore.exceptions.ProfileNotFound as err:
            print(str(err), file=sys.stderr)
            print("Available profiles: %s" %
                  ", ".join(sorted(session.available_profiles)), file=sys.stderr)
            sys.exit(-1)
        return session3
