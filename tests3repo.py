import os
import sys
import unittest
import uuid
import warnings


from s3repo.s3repomain import s3RepoMain

warnings.simplefilter("ignore", ResourceWarning)

"""
 Simple unit test that will test all exposed operations provided by S3Repo python program 
 
 This Unite test runs this test 
 
 Test case : test_all_operations
 
 1) Create one dummy user - this will create a user and create a Repo for user 
 2) Upload simple file (this file gets created part of "setUp" phase of unit test) to repo 
 3) List file all files from Repo 
 4) Download file from repo 
 5) Check download file ( uploaded and download file should have same content) 
 6) Delete user (this will delete user account and it's repo ) 
 7) Try to authenticate user again - it should fail as that user is now deleted ( negative test) 
"""


class TestS3RepoOperations(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestS3RepoOperations, self).__init__(*args, **kwargs)
        self.user_name = "dummyw9user"
        self.invalid_user_name = "Test_user"
        self.password = "thisis#Passw0rd"
        self.password_2 = "thisis$Passw0rd"
        self.email_id = "dummy_User@tibco.com"
        self.file_key = "my firstFile"
        self.input_file = "testfile.txt"
        self.input_file_text = uuid.uuid4().hex
        self.s3repo = s3RepoMain()

    def setUp(self):
        if not sys.warnoptions:
            import warnings
            warnings.simplefilter("ignore")

        #print("Creating input file with fixed text : [" + self.input_file_text + "]")
        file = open("testfile.txt", "w")
        file.write(self.input_file_text)
        file.close()

    def test_all_operations(self):
        print("###########################################")
        print("Running unit test: " + self._testMethodName)
        print("###########################################")
        self.assertEqual(self.s3repo.create_user(self.user_name, password=self.password, email_id=self.email_id), True,
                         "Create user "
                         "did not "
                         "return True")
        self.assertEqual(
            self.s3repo.uploadFile(self.user_name, self.password, "%s" % self.file_key, "%s" % self.input_file), True,
            "Upload file "
            "did not "
            "return True")
        self.assertEqual(self.s3repo.listFiles(self.user_name, self.password), True, "list user did not return True")
        self.assertEqual(self.s3repo.downloadFile(self.user_name, self.password, self.input_file), True,
                         "Download file did not "
                         "return True")
        self.assertEqual(self.checkFile(), True, "checkFile file did not "
                                                 "return True")
        self.assertEqual(self.s3repo.delete_user(self.user_name), True, "Delete user did not return True")
        self.assertRaises(ValueError, self.s3repo.authenticate_user, self.user_name, self.password)

    def test_invalid_user(self):
        print("###########################################")
        print("Running unit test: " + self._testMethodName)
        print("###########################################")
        self.assertRaises(RuntimeError, self.s3repo.create_user, self.invalid_user_name, password=self.password,
                          email_id=self.email_id)

    def test_change_password(self):
        print("###########################################")
        print("Running unit test: " + self._testMethodName)
        print("###########################################")
        self.assertEqual(self.s3repo.create_user(self.user_name, password=self.password, email_id=self.email_id), True,
                         "Create user "
                         "did not "
                         "return True")
        self.assertEqual(self.s3repo.authenticate_user(self.user_name, self.password), True, "authenticate_user did "
                                                                                             "not "
                                                                                             "return True")
        self.assertEqual(self.s3repo.create_user(self.user_name, password=self.password_2, email_id=self.email_id),
                         True,
                         "[Change password] Create user "
                         "did not "
                         "return True")
        self.assertEqual(self.s3repo.authenticate_user(self.user_name, self.password_2), True, "[Change password] "
                                                                                               "authenticate_user did "
                                                                                               "not "
                                                                                               "return True")
        self.assertEqual(self.s3repo.delete_user(self.user_name), True, "Delete user did not return True")

    def test_invalid_password(self):
        print("###########################################")
        print("Running unit test: " + self._testMethodName)
        print("###########################################")
        self.assertEqual(self.s3repo.create_user(self.user_name, password=self.password, email_id=self.email_id), True,
                         "Create user "
                         "did not "
                         "return True")
        self.assertEqual(self.s3repo.authenticate_user(self.user_name, self.password_2), False, "[Invalid password] "
                                                                                               "authenticate_user did "
                                                                                               "not "
                                                                                               "return True")
        self.assertEqual(self.s3repo.delete_user(self.user_name), True, "Delete user did not return True")

    def tearDown(self):
        if os.path.exists(self.input_file):
            os.remove(self.input_file)
        output_file = os.path.join(self.s3repo.output_folder, self.input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

    def checkFile(self):
        output_file = os.path.join(self.s3repo.output_folder, self.input_file)
        if os.path.exists(output_file):
            print("File Found")
            download_file_text = open(output_file, 'r').read()
            print(
                "Checking to see if uploaded file and download file has same fixed text [" + self.input_file_text + "]")
            if self.input_file_text in download_file_text:
                print("Files have same text - Success")
                return True
            else:
                return False
        else:
            return False


if __name__ == '__main__':
    unittest.main()
