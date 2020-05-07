import unittest
from jsonschema.exceptions import ValidationError
from typing import Dict
import logging
import os

from configuration.configuration import Configuration

logger = logging.getLogger('TestConfiguration')


class TestConfiguration(unittest.TestCase):
    test_data_path: str = os.path.join('test_data', 'test_configuration')

    def test_schema_validation(self):
        try:
            logger.info('Loading the correct Configuration..')
            Configuration(config_src=os.path.join(self.test_data_path, 'minimal_conf_correct.yml'),
                          config_schema_path=os.path.join('..', 'tests', self.test_data_path,
                                                          'minimal_yml_schema.json'))
        except ValidationError as e:
            logger.error('Error validating the correct yml: %s', e)
            self.fail('Error validating the correct yml')
        else:
            logger.info('First yml validated successfully.')

        with self.assertRaises(ValidationError):
            logger.info('Loading the wrong Configuration..')
            Configuration(config_src=os.path.join(self.test_data_path, 'minimal_conf_wrong.yml'))
        logger.info('Second yml failed to validate successfully.')

    def test_to_json(self):
        logger.info('Loading Configuration..')
        configuration = Configuration(config_src=os.path.join(self.test_data_path, 'template_conf.yml'))
        expected_json = {'aws': [{'config':
                                      {'access_key': 'access_key_1',
                                       'secret_key': 'secret_key_1',
                                       'instance_id': 'instance_id_1',
                                       'ec2_region': 'ec2_region_1',
                                       'ec2_amis': ['ec2_ami_1'],
                                       'ec2_keypair': 'ec2_keypair_1',
                                       'ec2_secgroups': ['ec2_secgroup_1'],
                                       'ec2_instancetype': 'ec2_instancetype_1'}
                                  }],
                         'mineserver': [{'config':
                                             {'ssh_key_file_path': 'ssh_key_file_path_1',
                                              'memory_allocation': 'memory_allocation_1'}
                                         }],
                         'web_client': [{'config':
                                             {'server_password': 'server_password_1'}
                                         }]
                         }
        # Compare
        logger.info('Comparing the results..')
        self.assertDictEqual(self._sort_dict(expected_json), self._sort_dict(configuration.to_json()))

    def test_to_yaml(self):
        logger.info('Loading Configuration..')
        configuration = Configuration(config_src=os.path.join(self.test_data_path, 'template_conf.yml'))
        # Modify and export yml
        logger.info('Changed the host and the api_key..')
        configuration.aws[0]['config']['access_key'] = 'access_key_2'
        configuration.mineserver[0]['config']['ssh_key_file_path'] = 'ssh_key_file_path_2'
        logger.info('Exporting to yaml..')
        configuration.to_yaml('test_data/test_configuration/actual_output_to_yaml.yml')
        # Load the modified yml
        logger.info('Loading the exported yaml..')
        modified_configuration = Configuration(
            config_src=os.path.join(self.test_data_path, 'actual_output_to_yaml.yml'))
        # Compare
        logger.info('Comparing the results..')
        expected_json = {'aws': [{'config':
                                      {'access_key': 'access_key_2',
                                       'secret_key': 'secret_key_1',
                                       'instance_id': 'instance_id_1',
                                       'ec2_region': 'ec2_region_1',
                                       'ec2_amis': ['ec2_ami_1'],
                                       'ec2_keypair': 'ec2_keypair_1',
                                       'ec2_secgroups': ['ec2_secgroup_1'],
                                       'ec2_instancetype': 'ec2_instancetype_1'}
                                  }],
                         'mineserver': [{'config':
                                             {'ssh_key_file_path': 'ssh_key_file_path_2',
                                              'memory_allocation': 'memory_allocation_1'}
                                         }],
                         'web_client': [{'config':
                                             {'server_password': 'server_password_1'}
                                         }]
                         }
        self.assertDictEqual(self._sort_dict(expected_json), self._sort_dict(modified_configuration.to_json()))

    @classmethod
    def _sort_dict(cls, dictionary: Dict) -> Dict:
        return {k: cls._sort_dict(v) if isinstance(v, dict) else v
                for k, v in sorted(dictionary.items())}

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
        pass

    def tearDown(self) -> None:
        pass

    @classmethod
    def setUpClass(cls):
        cls._setup_log()

    @classmethod
    def tearDownClass(cls):
        pass


if __name__ == '__main__':
    unittest.main()
