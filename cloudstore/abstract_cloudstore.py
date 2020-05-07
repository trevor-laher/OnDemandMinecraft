from abc import ABC, abstractmethod


class AbstractCloudstore(ABC):
    __slots__ = ('_handler',)

    @abstractmethod
    def __init__(self, *args, **kwargs) -> None:
        """
        Tha basic constructor. Creates a new instance of Cloudstore using the specified credentials
        """

        pass

    @staticmethod
    @abstractmethod
    def get_handler(*args, **kwargs):
        """
        Returns a Cloudstore handler.

        :param args:
        :param kwargs:
        :return:
        """

        pass

    @abstractmethod
    def upload_file(self, *args, **kwargs):
        """
        Uploads a file to the Cloudstore

        :param args:
        :param kwargs:
        :return:
        """

        pass

    @abstractmethod
    def download_file(self, *args, **kwargs):
        """
        Downloads a file from the Cloudstore

        :param args:
        :param kwargs:
        :return:
        """

        pass

    @abstractmethod
    def delete_file(self, *args, **kwargs):
        """
        Deletes a file from the Cloudstore

        :param args:
        :param kwargs:
        :return:
        """

        pass

    @abstractmethod
    def ls(self, *args, **kwargs):
        """
        List the files and folders in the Cloudstore
        :param args:
        :param kwargs:
        :return:
        """
        pass
