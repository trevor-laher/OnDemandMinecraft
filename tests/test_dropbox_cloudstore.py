import unittest
import os
import random
import string
import logging
import copy
from typing import Tuple
from dropbox.exceptions import BadInputError

from configuration.configuration import Configuration
from cloudstore.dropbox_cloudstore import DropboxCloudstore

logger = logging.getLogger('TestDropboxCloudstore')


class TestDropboxCloudstore(unittest.TestCase):
    __slots__ = ('configuration', 'file_name')

    configuration: Configuration
    file_name: str
    test_data_path: str = os.path.join('test_data', 'test_dropbox_cloudstore')

    def test_connect(self):
        # Test the connection with the correct api key
        try:
            cloud_store_correct_key = DropboxCloudstore(config=self.configuration.get_cloudstore_configs()[0])
            cloud_store_correct_key.ls()
        except BadInputError as e:
            logger.error('Error connecting with the correct credentials: %s', e)
            self.fail('Error connecting with the correct credentials')
        else:
            logger.info('Connected with the correct credentials successfully.')
        # Test that the connection is failed with the wrong credentials
        with self.assertRaises(BadInputError):
            cloud_store_wrong_configuration = copy.deepcopy(self.configuration.get_cloudstore_configs()[0])
            cloud_store_wrong_configuration['api_key'] = 'wrong_key'
            cloud_store_wrong_key = DropboxCloudstore(config=cloud_store_wrong_configuration)
            cloud_store_wrong_key.ls()
        logger.info("Loading Dropbox with wrong credentials failed successfully.")

    def test_upload_download(self):
        cloud_store = DropboxCloudstore(config=self.configuration.get_cloudstore_configs()[0])
        # Upload file
        logger.info('Uploading file..')
        file_to_upload = open(os.path.join(self.test_data_path, self.file_name), 'rb').read()
        cloud_store.upload_file(file_to_upload, self.file_name)
        # Check if it was uploaded
        self.assertIn(self.file_name, cloud_store.ls().keys())
        # Download it
        logger.info('Downloading file..')
        cloud_store.download_file(fromfile=self.file_name,
                                  tofile=os.path.join(self.test_data_path, 'actual_downloaded.txt'))
        # Compare contents of downloaded file with the original
        self.assertEqual(open(os.path.join(self.test_data_path, self.file_name), 'rb').read(),
                         open(os.path.join(self.test_data_path, 'actual_downloaded.txt'), 'rb').read())

    def test_upload_delete(self):
        cloud_store = DropboxCloudstore(config=self.configuration.get_cloudstore_configs()[0])
        # Upload file
        logger.info('Uploading file..')
        file_to_upload = open(os.path.join(self.test_data_path, self.file_name), 'rb').read()
        cloud_store.upload_file(file_to_upload, self.file_name)
        # Check if it was uploaded
        self.assertIn(self.file_name, cloud_store.ls().keys())
        # Delete it
        cloud_store.delete_file(self.file_name)
        # Check if it was deleted
        self.assertNotIn(self.file_name, cloud_store.ls().keys())

    @staticmethod
    def _generate_random_filename_and_contents() -> Tuple[str, str]:
        letters = string.ascii_lowercase
        file_name = ''.join(random.choice(letters) for _ in range(10)) + '.txt'
        contents = ''.join(random.choice(letters) for _ in range(20))
        return file_name, contents

    @staticmethod
    def _setup_log() -> None:
        # noinspection PyArgumentList
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            handlers=[logging.StreamHandler()
                                      ]
                            )

    def setUp(self) -> None:
        self.file_name, contents = self._generate_random_filename_and_contents()
        with open(os.path.join(self.test_data_path, self.file_name), 'a') as f:
            f.write(contents)

    def tearDown(self) -> None:
        os.remove(os.path.join(self.test_data_path, self.file_name))

    @classmethod
    def setUpClass(cls):
        cls._setup_log()
        if "DROPBOX_API_KEY" not in os.environ:
            logger.error('DROPBOX_API_KEY env variable is not set!')
            raise Exception('DROPBOX_API_KEY env variable is not set!')
        logger.info('Loading Configuration..')
        cls.configuration = Configuration(config_src=os.path.join(cls.test_data_path, 'template_conf.yml'))

    @classmethod
    def tearDownClass(cls):
        cloud_store = DropboxCloudstore(config=cls.configuration.get_cloudstore_configs()[0])
        cloud_store.delete_file()


if __name__ == '__main__':
    unittest.main()
