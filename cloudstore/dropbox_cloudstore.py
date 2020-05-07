from typing import Dict, Union
import logging
import os
from dropbox import Dropbox, files, exceptions

from .abstract_cloudstore import AbstractCloudstore

logger = logging.getLogger('DropboxCloudstore')


class DropboxCloudstore(AbstractCloudstore):
    __slots__ = ('_handler', 'remote_folder')

    _handler: Dropbox
    remote_folder: str

    def __init__(self, config: Dict) -> None:
        """
        The basic constructor. Creates a new instance of Cloudstore using the specified credentials

        :param config:
        """

        self._handler = self.get_handler(api_key=config['api_key'])
        self.remote_folder = os.sep + config['remote_folder'] + os.sep
        super().__init__()

    @staticmethod
    def get_handler(api_key: str) -> Dropbox:
        """
        Returns a Cloudstore handler.

        :param api_key:
        :return:
        """

        dbx = Dropbox(api_key)
        return dbx

    def upload_file(self, file_bytes: bytes, upload_path: str, write_mode: str = 'overwrite') -> None:
        """
        Uploads a file to the Cloudstore

        :param file_bytes:
        :param upload_path:
        :param write_mode:
        :return:
        """

        upload_path = self.remote_folder + upload_path

        try:
            logger.debug("Uploading file to path: %s" % upload_path)
            self._handler.files_upload(f=file_bytes, path=upload_path, mode=files.WriteMode(write_mode))
        except exceptions.ApiError as err:
            logger.error('API error: %s' % err)

    def download_file(self, fromfile: str, tofile: str = None) -> Union[bytes, None]:
        """
        Downloads a file from the Cloudstore

        :param fromfile:
        :param tofile:
        :return:
        """

        fromfile = self.remote_folder + fromfile

        try:
            if tofile is not None:
                logger.debug("Downloading file from path: %s to path %s" % (fromfile, tofile))
                self._handler.files_download_to_file(download_path=tofile, path=fromfile)
            else:
                logger.debug("Downloading file from path: %s to variable" % fromfile)
                md, res = self._handler.files_download(path=fromfile)
                data = res.content  # The bytes of the file
                return data
        except exceptions.HttpError as err:
            logger.error('HTTP error %s' % err)
            return None

    def delete_file(self, file_path: str = '') -> None:
        """
        Deletes a file from the Cloudstore

        :param file_path:
        :return:
        """

        file_path = self.remote_folder + file_path
        try:
            logger.debug("Deleting file from path: %s" % file_path)
            self._handler.files_delete_v2(path=file_path)
        except exceptions.ApiError as err:
            logger.error('API error %s' % err)

    def ls(self, path: str = '') -> Dict:
        """
        List the files and folders in the Cloudstore

        :param path:
        :return:
        """

        path = self.remote_folder + path

        try:
            files_list = self._handler.files_list_folder(path=path)
            files_dict = {}
            for entry in files_list.entries:
                files_dict[entry.name] = entry
            return files_dict
        except exceptions.ApiError as err:
            logger.error('Folder listing failed for %s -- assumed empty: %s' % (path, err))
            return {}
