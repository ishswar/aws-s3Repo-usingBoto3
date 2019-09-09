#!/usr/bin/env python3
import logging
import os
import re
import time

from prettytable import PrettyTable

from botocore.exceptions import ClientError
from s3repo.helper.ProgressPercentage import ProgressPercentage
from s3repo.helper import awsGetConnection, password_helper, logger_setup
from s3repo.helper.awsGetConnection import awsHelper


def validate_bucket_Name(bucket_name):
    """
    Validate bucket name as per AWS S3 guidelines
    :param bucket_name:
    :return: True if valid else false
    """
    # Regex that matches rules at
    # https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-s3-bucket-naming-requirements.html

    pattern = '(?=^.{3,63}$)(?!^(\d+\.)+\d+$)(^(([a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])\.)*([a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])$)'
    result = re.match(pattern, bucket_name)
    if result:
        return True
    else:
        return False


class s3RepoMain:

    def __init__(self):
        # logging setup ( default is Debug )
        self.logger = logger_setup.logger
        self.logger.name = "s3repo.s3repomain"
        # System bucket that will hold all user information (username , password )
        self.usersBucket = "ucsc-users.hw9"

        # De-facto Repo admin user
        # This is used mainly for maintenance of Repo
        self.admin_username = "s3w9admin"
        self.admin_password = "admin123"
        self.admin_email = "s3admin@s3users.com"
        # When user tries to download file from Repo it will be sored here
        self.output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../output/")

        # AWS S3 info
        self.region = "us-west-2"
        self.profile = "default"  # "SharedAccount"
        aws_helper = awsHelper(self.region, self.profile)
        self.session = aws_helper.get_aws_connection()  # boto3 object
        self.s3 = self.session.resource('s3')  # boto3 object

    def init_users_bucket(self):
        """
        Create S3 bucket to hold all repo users ( we will store users information - username / passwords ) in it
        Also create a bootstrap admin user that will be used for maintenance
        :return:
        """
        try:
            isBucketThere = self.bucket_name_available(self.usersBucket)
            if isBucketThere:
                logging.debug("Bucket [" + self.usersBucket + "] already there no need to re-create it")
            else:
                self.create_userBucket(self.usersBucket)  # will create user info repo
                # Create a bootstrap / admin user for management
                did_we_create_admin_user = self.create_user(self.admin_username, self.admin_password,
                                                            self.admin_email)  # will create bootstrap user
                if did_we_create_admin_user:
                    logging.info("Admin user has been created successfully")

            return True
        except Exception as e:
            self.logger.error("Error creating users repo" + str(e))
            raise e

    def bucket_name_available(self, bucket_name=None):
        """
        Check if S3 buck exists with given name
        :param bucket_name: bucket name to check in S3 (bucket names are global)
        :return: True if bucket name does not exists ; else False
        """
        try:
            self.s3.meta.client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            if "403" in str(e.response):
                raise RuntimeWarning("Repo [" + bucket_name + "] already present - can't us this name")
            # print(str(e))
            return False

    def create_userBucket(self, bucket_name):
        """
        Create S3 bucket to hold all files uploaded by user
        :param bucket_name:
        :return:
        """
        try:
            isBucketThere = self.bucket_name_available(bucket_name)
            if isBucketThere:
                logging.debug("Bucket [" + bucket_name + "] already there no need to re-create it")
                return True
            else:
                s3_client = self.session.client('s3', region_name=self.region)
                location = {'LocationConstraint': self.region}
                s3_client.create_bucket(Bucket=bucket_name,
                                        CreateBucketConfiguration=location)

                try:
                    time.sleep(8)  # Sleep before we check if bucket has been created successfully
                    self.s3.meta.client.head_bucket(Bucket=bucket_name)
                    self.logger.info("Repo [" + bucket_name + "] has been created successfully")

                    return True
                except ClientError as e:
                    logging.error("Failed to create a user repo :" + str(e.response))
                    return False

        except Exception as e:
            raise e

    def delete_userBucket(self, bucket_name):
        """
        Delete user bucket - but before that we will have to delete all files/objects in bucket one by one
        :param bucket_name:
        :return:
        """
        isBucketThere = self.bucket_name_available(bucket_name)
        if isBucketThere:
            try:
                # s3_client = session.client('s3', region_name=region)
                bucket = self.s3.Bucket(bucket_name)
                bucket.objects.all().delete()
                bucket.delete()
                # s3_client.delete_bucket(Bucket=bucket_name)
                self.logger.info("Repo [" + bucket_name + "] has been deleted")
                return True
            except ClientError as e:
                self.logger.info(
                    ("User [" + bucket_name + "] does not have any repo so skipping it's repo delete part"))
                self.logger.info(e.response)
                return True
            except ClientError as e:
                logging.error(e)
                return False
        else:
            self.logger.info("Repo [" + bucket_name + "] does not exists - no need to delete it")
            return True

    def create_user(self, user_name, password, email_id):
        """
        Add one file (entry) in users bucket that holds all the information regarding this user - but as Metadata
        the file has 0 bytes content
        :param user_name: This has to be valid S3 bucket name
        :param password:
        :param email_id:
        :return: Return true if user has been created successfully else false
        """
        self.logger.info(("About to create user [" + user_name + "]"))
        if validate_bucket_Name(user_name):
            try:
                self.init_users_bucket()

                if user_name != self.admin_username:  # Admin user does not need to have Repo / bucket to store file
                    self.create_userBucket(user_name)

                s3_client = self.session.client('s3', region_name=self.region)

                open(user_name, 'a').close()  # Create a zero byte file on system

                # Users password is stored as has using helper method that will hash the user password as sha256
                s3_client.upload_file(
                    user_name, self.usersBucket, user_name,  # upload zero byte file to S3 but set user info as Metadata
                    ExtraArgs={"Metadata": {'password': password_helper.hash_password(password), 'email': email_id}}
                )

                # Check to see if user has been inserted in users bucket
                response = s3_client.head_object(
                    Bucket=self.usersBucket,
                    Key=user_name,
                )

                # Cleanup zero byte file
                if os.path.exists(user_name):
                    os.remove(user_name)
                else:
                    self.logger.warning("The temporary file does not exist - ignoring it deleting")

                self.logger.info("User [" + user_name + "] has been created/updated in repo")
                return True
            except RuntimeWarning as rw:
                if "Repo already present" in str(rw):
                    logging.warning("Username/Repo [" + user_name + "] already exists - use different username ")
                    return False
            except Exception as e:
                self.logger.error("Error while creating user [" + user_name + "], Error: " + str(e.response))
                return False
        else:
            self.logger.error(
                "Invalid bucket name - check rules at https://docs.aws.amazon.com/awscloudtrail/latest/userguide"
                "/cloudtrail-s3-bucket-naming-requirements.html")
            raise RuntimeError("User name [" + user_name + "] is invalid as per S3 rules")

    def delete_user(self, user_name):
        """
        Delete user - first we delete user bucket that has all the files for repo
        once that is done we remove user from users repo / buck as well
        :param user_name:
        :return:
        """
        s3_client = self.session.client('s3', region_name=self.region)

        if self.delete_userBucket(user_name):
            response = s3_client.delete_object(Bucket=self.usersBucket, Key=user_name)
            self.logger.info("User [" + user_name + "] & and it's repo content has been deleted from repo")
            return True
        else:
            self.logger.error("Error whiling deleting user [" + user_name + "]")
            return False

    def authenticate_user(self, user_name, user_password):
        """
        Compare on-way has from what user provided via user_password and what is hash in users repo
        if they match password is good else bad password
        :param user_name:
        :param user_password:
        :return:
        """
        s3_client = self.session.client('s3', region_name=self.region)
        try:
            response = s3_client.head_object(
                Bucket=self.usersBucket,
                Key=user_name,
            )

            try:
                if password_helper.check_password(response["Metadata"]["password"], user_password):
                    self.logger.debug("User [" + user_name + "] has been authenticated successfully")
                    return True
                else:
                    self.logger.debug("Failed to authenticate user [" + user_name + "]")
                    return False
            except KeyError as e:
                self.logger.info("Required key is missing in metadata - this is unexpected error")
        except ClientError as e:
            if '404' in str(e.response):
                self.logger.info("User [" + user_name + "] does not exists - create it first")
                raise ValueError("User [" + user_name + "] not found")
            else:
                self.logger.info(e)

    def uploadFile(self, user_name, user_password, file_key, file):
        """
        This method enable user to upload the file to users Repo ( S3 bucket )
        While file is getting uploaded we use progress Percentage call to print upload progress
        :param user_name:
        :param user_password:
        :param file_key:
        :param file:
        :return:
        """
        if os.path.isfile(file):
            try:
                if self.authenticate_user(user_name, user_password):
                    s3_client = self.session.client('s3', region_name=self.region)
                    self.logger.info(("About to upload file [" + file + "]"))
                    fileNamekey = os.path.basename(file);
                    s3_client.upload_file(
                        file, user_name, fileNamekey,
                        Callback=ProgressPercentage(file)
                    )

                    response = s3_client.put_object_tagging(
                        Bucket=user_name,
                        Key=fileNamekey,
                        Tagging={
                            'TagSet': [
                                {
                                    'Key': 'user-key',
                                    'Value': file_key
                                },
                            ]
                        }
                    )
                    response = s3_client.head_object(
                        Bucket=user_name,
                        Key=fileNamekey,
                    )
                    print("\n\r")
                    self.logger.info("File [" + file + "] has been uploaded successfully")
                    return True
                else:
                    logging.error("User authentication failed for user: " + user_name)
                    return False
            except ValueError as ve:
                if "not found" in str(ve):
                    self.logger.error(str(ve))
                    return False
                else:
                    self.logger.error(str(ve))
                    return False
        else:
            self.logger.error("file [" + file + "] does not exists")
            return False

    def listFiles(self, bucket_name, user_password):
        """
        This will list all files stored in user's Repo ( S3 bucket ) - listing will happen using python module PrettyTable
        TO DO : Actually we should return list of file and caller method should use prettyTable or whatever they need
        to print the data
        :param bucket_name:
        :param user_password:
        :return:
        """
        try:
            if self.authenticate_user(bucket_name, user_password):
                if self.bucket_name_available(bucket_name):
                    try:
                        bucket = self.s3.Bucket(bucket_name)
                        x = PrettyTable()
                        logging.info("Printing content of Repo: " + bucket_name)
                        x.field_names = ["File", "User key/Tag", "lastModified", "Size"]
                        bucketContent = bucket.objects.all();
                        bHasFiles = False
                        for my_bucket_object in bucket.objects.all():
                            bHasFiles = True
                            # For this object/key get tag set by user
                            s3_client = self.session.client('s3', region_name=self.region)
                            response = s3_client.get_object_tagging(
                                Bucket=bucket_name,
                                Key=my_bucket_object.key
                            )
                            tag_set = response["TagSet"]
                            user_tag = ""
                            for tag in tag_set:
                                if tag["Key"] == "user-key":
                                    user_tag = tag["Value"]

                            x.add_row(
                                [my_bucket_object.key, user_tag, my_bucket_object.last_modified, my_bucket_object.size])

                        if bHasFiles:
                            print(x)
                            return True
                        else:
                            self.logger.warning("User's repo is empty")
                            return False

                    except ClientError as e:
                        self.logger.error(e.response)
                else:
                    logging.error("Repo [" + bucket_name + "] does not exists")
            else:
                logging.error("User authentication failed for user: " + bucket_name)
                return False
        except ValueError as ve:
            if "not found" in str(ve):
                self.logger.error(str(ve))
                return False

    def getFile(self, bucket_name, user_password, user_Key, output_location):
        """
        Given user-key / tag find a file in user's repo and download it to given location
        :param output_location:
        :param user_Key:
        :param bucket_name:
        :param user_password:
        :return:
        """
        try:
            if self.authenticate_user(bucket_name, user_password):
                if self.bucket_name_available(bucket_name):
                    try:
                        bucket = self.s3.Bucket(bucket_name)
                        user_Key = str.strip(user_Key)
                        did_we_foundFile = False
                        for my_bucket_object in bucket.objects.all():
                            # For this object/key get tag set by user
                            s3_client = self.session.client('s3', region_name=self.region)
                            response = s3_client.get_object_tagging(
                                Bucket=bucket_name,
                                Key=my_bucket_object.key
                            )
                            tag_set = response["TagSet"]
                            for tag in tag_set:
                                if tag["Key"] == "user-key":
                                    if user_Key == tag["Value"]:
                                        did_we_foundFile = True
                                        output_location = str.strip(output_location)
                                        if not len(output_location) > 0:
                                            self.logger.warning("User provided empty location for output location - we "
                                                                "will use default location [" + self.output_folder + "]")
                                            output_location = "--"
                                        self.logger.info(
                                            "Found file [" + my_bucket_object.key + "] for provided user-key [" + user_Key + "]")
                                        return self.downloadFile(bucket_name, user_password, my_bucket_object.key,
                                                                 skip_auth=True, output_location=output_location)

                        if not did_we_foundFile:
                            logging.warning("No file found matching user key [" + user_Key + "]")
                            return False

                    except ClientError as e:
                        self.logger.error(e.response)
                else:
                    logging.error("Repo [" + bucket_name + "] does not exists")
                    return False
            else:
                logging.error("User authentication failed for user: " + bucket_name)
                return False
        except ValueError as ve:
            if "not found" in str(ve):
                self.logger.error(str(ve))
                return False

    def downloadFile(self, user_name, user_password, file_name, output_location="--", skip_auth=False):
        """
        Download file from users Repo ( S3 bucket )
        It  will download file in fixed location 'download_to_this_folder' defined as constant
        If file with same name present it will give you warning - but at same time it will overwrite it
        :param output_location:
        :param skip_auth:
        :param user_name:
        :param user_password:
        :param file_name:
        :return:
        """
        checkUserAuth = True if skip_auth else self.authenticate_user(user_name, user_password)
        try:
            if checkUserAuth:
                if not os.path.exists(self.output_folder):
                    os.makedirs(self.output_folder)

                if output_location == "--":
                    # download_to_this_folder = self.output_folder + file_name
                    download_to_this_folder = os.path.join(self.output_folder, file_name)
                else:
                    if os.path.exists(output_location):
                        download_to_this_folder = os.path.join(output_location,
                                                               file_name)  # output_location + file_name
                    else:
                        self.logger.error("Output folder [" + output_location + "] does not exists create it first ")
                        return False

                if os.path.isfile(download_to_this_folder):
                    self.logger.warning(
                        "File [" + file_name + "] already exists in location [" + self.output_folder + "] it will "
                                                                                                       "be "
                                                                                                       "overwritten")

                try:
                    self.s3.Bucket(user_name).download_file(file_name, download_to_this_folder)
                    if os.path.isfile(download_to_this_folder):
                        self.logger.info(
                            "File [" + file_name + "] has been downloaded to: [" + download_to_this_folder + "]")
                    return True
                except ClientError as e:
                    if '404' in str(e.response):
                        self.logger.info("File [" + file_name + "] does not exists - upload it first")
                    else:
                        self.logger.info(e)
            else:
                self.logger.error("User authentication failed for user: " + user_name)
        except ValueError as ve:
            if "not found" in str(ve):
                self.self.logger.error(str(ve))
                return False

    def deleteFile(self, bucket_name, user_password, user_Key):
        """
        Given user-key / tag find a file in user's repo and delete it to given location
        :param user_Key:
        :param bucket_name:
        :param user_password:
        :return:
        """
        try:
            if self.authenticate_user(bucket_name, user_password):
                if self.bucket_name_available(bucket_name):
                    try:
                        bucket = self.s3.Bucket(bucket_name)
                        user_Key = str.strip(user_Key)
                        did_we_foundFile = False
                        for my_bucket_object in bucket.objects.all():
                            # For this object/key get tag set by user
                            s3_client = self.session.client('s3', region_name=self.region)
                            response = s3_client.get_object_tagging(
                                Bucket=bucket_name,
                                Key=my_bucket_object.key
                            )
                            tag_set = response["TagSet"]
                            for tag in tag_set:
                                if tag["Key"] == "user-key":
                                    if user_Key == tag["Value"]:
                                        did_we_foundFile = True
                                        return self.deleteFileInBucket(bucket_name,user_password,my_bucket_object.key,skip_auth=True)

                        if not did_we_foundFile:
                            logging.warning("No file found matching user key [" + user_Key + "]")
                            return False

                    except ClientError as e:
                        self.logger.error(e.response)
                else:
                    logging.error("Repo [" + bucket_name + "] does not exists")
                    return False
            else:
                logging.error("User authentication failed for user: " + bucket_name)
                return False
        except ValueError as ve:
            if "not found" in str(ve):
                self.logger.error(str(ve))
                return False

    def deleteFileInBucket(self, user_name, user_password, file_name, skip_auth=False):
        """
        Delete object from users repo
        :param skip_auth:
        :param user_name:
        :param user_password:
        :param file_name:
        :return:
        """
        checkUserAuth = True if skip_auth else self.authenticate_user(user_name, user_password)
        try:
            if checkUserAuth:
                try:
                    s3_client = self.session.client('s3', region_name=self.region)
                    s3_client.delete_object(Bucket=user_name, Key=file_name)
                    self.logger.info(
                        "File [" + file_name + "] has been deleted")
                    return True
                except ClientError as e:
                    if '404' in str(e.response):
                        self.logger.info("File [" + file_name + "] does not exists - upload it first")
                    else:
                        self.logger.info(e)
            else:
                self.logger.error("User authentication failed for user: " + user_name)
        except ValueError as ve:
            if "not found" in str(ve):
                self.self.logger.error(str(ve))
                return False

    def tear_down_all(self, _admin_password):
        """
        This is a special method that will tear down all the S3 buckets that this program has created
        This can be used to cleanup
        ***************** BE MINDFUL WHEN USING THIS METHOD ******************
        :param _admin_password:
        :return:
        """
        try:
            logging.warning("About to destroy all users and user repo")
            if self.authenticate_user(self.admin_username, _admin_password):
                if self.bucket_name_available(self.usersBucket):
                    try:
                        bucket = self.s3.Bucket(self.usersBucket)
                        x = PrettyTable()
                        logging.info("Printing content of Repo: " + self.usersBucket)
                        x.field_names = ["File", "lastModified", "Size", "deleted?"]
                        bHasFiles = False
                        for my_bucket_object in bucket.objects.all():
                            bHasFiles = True
                            did_we_delete = self.delete_userBucket(my_bucket_object.key)
                            x.add_row(
                                [my_bucket_object.key, my_bucket_object.last_modified, my_bucket_object.size,
                                 did_we_delete])

                        if bHasFiles:
                            print(x)
                            logging.warning("About to destroy main user repo")
                            self.delete_userBucket(self.usersBucket)
                            logging.info("Tear down complete")
                            return True
                        else:
                            self.logger.warning("User's repo is empty")

                    except ClientError as e:
                        self.logger.error(e.response)
                else:
                    self.logger.error("Repo [" + self.usersBucket + "] does not exists")
            else:
                self.logger.error("User authentication failed for user: " + self.admin_username)
                return False
        except ValueError as ve:
            if "not found" in str(ve):
                self.logger.error(str(ve))
                return False
