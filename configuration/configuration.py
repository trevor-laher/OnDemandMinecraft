import os
import logging
from typing import Dict, List, Tuple, Union
import json
import _io
from io import StringIO, TextIOWrapper
import re
import yaml
from jsonschema import validate as validate_json_schema

logger = logging.getLogger('Configuration')


class Configuration:
    __slots__ = ('config', 'config_path', 'aws', 'mineserver', 'web_client')

    config: Dict
    config_path: str
    aws: Dict
    mineserver: Dict
    web_client: Dict
    config_attributes: List = list()
    env_variable_tag: str = '!ENV'
    env_variable_pattern: str = r'.*?\${(\w+)}.*?'  # ${var}

    def __init__(self, config_src: Union[TextIOWrapper, StringIO, str], config_schema_path: str = 'yml_schema.json'):
        """
        The basic constructor. Creates a new instance of the Configuration class.

        :param config_src:
        :param config_schema_path:
        """

        # Load the predefined schema of the configuration
        configuration_schema = self.load_configuration_schema(config_schema_path=config_schema_path)
        # Load the configuration
        self.config, self.config_path = self.load_yml(config_src=config_src,
                                                      env_tag=self.env_variable_tag,
                                                      env_pattern=self.env_variable_pattern)
        logger.debug("Loaded config: %s" % self.config)
        # Validate the config
        validate_json_schema(self.config, configuration_schema)
        # Set the config properties as instance attributes
        all_config_attributes = ('aws', 'mineserver', 'web_client')
        for config_attribute in all_config_attributes:
            if config_attribute in self.config.keys():
                setattr(self, config_attribute, self.config[config_attribute])
                self.config_attributes.append(config_attribute)
            else:
                setattr(self, config_attribute, None)

    @staticmethod
    def load_configuration_schema(config_schema_path: str) -> Dict:
        with open('/'.join([os.path.dirname(os.path.realpath(__file__)), config_schema_path])) as f:
            configuration_schema = json.load(f)
        return configuration_schema

    @staticmethod
    def load_yml(config_src: Union[TextIOWrapper, StringIO, str], env_tag: str, env_pattern: str) -> Tuple[Dict, str]:
        pattern = re.compile(env_pattern)
        loader = yaml.SafeLoader
        loader.add_implicit_resolver(env_tag, pattern, None)

        def constructor_env_variables(loader, node):
            """
            Extracts the environment variable from the node's value
            :param yaml.Loader loader: the yaml loader
            :param node: the current node in the yaml
            :return: the parsed string that contains the value of the environment
            variable
            """
            value = loader.construct_scalar(node)
            match = pattern.findall(value)  # to find all env variables in line
            if match:
                full_value = value
                for g in match:
                    full_value = full_value.replace(
                        f'${{{g}}}', os.environ.get(g, g)
                    )
                return full_value
            return value

        loader.add_constructor(env_tag, constructor_env_variables)

        if isinstance(config_src, TextIOWrapper):
            logging.debug("Loading yaml from TextIOWrapper")
            config = yaml.load(config_src, Loader=loader)
            config_path = config_src.name
        elif isinstance(config_src, StringIO):
            logging.debug("Loading yaml from StringIO")
            config = yaml.load(config_src, Loader=loader)
            config_path = "StringIO"
        elif isinstance(config_src, str):
            logging.debug("Loading yaml from path")
            with open(config_src) as f:
                config = yaml.load(f, Loader=loader)
            config_path = config_src
        else:
            raise TypeError('Config file must be TextIOWrapper or path to a file')
        return config, config_path

    def get_aws_configs(self) -> List:
        if 'aws' in self.config_attributes:
            return [sub_config['config'] for sub_config in self.aws]
        else:
            raise ConfigurationError('Config property aws not set!')

    def get_mineserver_configs(self) -> List:
        if 'mineserver' in self.config_attributes:
            return [sub_config['config'] for sub_config in self.mineserver]
        else:
            raise ConfigurationError('Config property mineserver not set!')

    def get_web_client_configs(self) -> List:
        if 'web_client' in self.config_attributes:
            return [sub_config['config'] for sub_config in self.web_client]
        else:
            raise ConfigurationError('Config property web_client not set!')

    def to_yml(self, fn: Union[str, _io.TextIOWrapper]) -> None:
        """
        Writes the configuration to a stream. For example a file.

        :param fn:
        :return:
        """

        dict_conf = dict()
        for config_attribute in self.config_attributes:
            dict_conf[config_attribute] = getattr(self, config_attribute)

        if isinstance(fn, str):
            with open(fn, 'w') as f:
                yaml.dump(dict_conf, f, default_flow_style=False)
        elif isinstance(fn, _io.TextIOWrapper):
            yaml.dump(dict_conf, fn, default_flow_style=False)
        else:
            raise TypeError('Expected str or _io.TextIOWrapper not %s' % (type(fn)))

    to_yaml = to_yml

    def to_json(self) -> Dict:
        dict_conf = dict()
        for config_attribute in self.config_attributes:
            dict_conf[config_attribute] = getattr(self, config_attribute)
        return dict_conf

    def __getitem__(self, item):
        return self.__getattribute__(item)


class ConfigurationError(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
