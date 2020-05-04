from flask import Flask, render_template, request
from flask_cors import CORS
from multiprocessing import Process
from configuration.configuration import Configuration
import logging
import logging.handlers
import argparse
import boto3
import time
import paramiko
import os

app = Flask(__name__)
CORS(app)


def _setup_log(log_path: str = 'logs/output.log', debug: bool = False) -> None:
    log_path = log_path.split(os.sep)
    if len(log_path) > 1:

        try:
            os.makedirs((os.sep.join(log_path[:-1])))
        except FileExistsError:
            pass
    log_filename = os.sep.join(log_path)
    # noinspection PyArgumentList
    logging.basicConfig(level=logging.INFO if debug is not True else logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        handlers=[
                            logging.handlers.TimedRotatingFileHandler(log_filename, when='midnight', interval=1),
                            logging.StreamHandler()
                        ]
                        )


def _argparser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='An AWS hosted Minecraft server that will only run when players are active. '
                    'Players can start the server through a simple UI accessed through free Heroku server hosting.',
        add_help=False)
    # Required Args
    required_arguments = parser.add_argument_group('Required Arguments')
    config_file_params = {
        'type': argparse.FileType('r'),
        'required': True,
        'help': "The configuration yml file"}

    required_arguments.add_argument('-c', '--config-file', **config_file_params)
    # Optional args
    optional = parser.add_argument_group('Optional Arguments')
    optional.add_argument('-r', '--run-mode', help="The type of operation desired to run",
                          choices=['run_flask', 'create_instance'], default='run_flask')
    optional.add_argument('-l', '--log', help="Name of the output log file", default='logs/out.log')
    optional.add_argument('-d', '--debug', action='store_true', help='Enables the debug log messages')
    optional.add_argument("-h", "--help", action="help", help="Show this help message and exit")

    return parser.parse_args()


class Mineserver:
    __slots__ = ('instance_id', 'memory_allocation')

    instance_id: str
    memory_allocation: str

    def __init__(self, instance_id: str, memory_allocation: str) -> None:
        """
        The basic constructor. Creates a new instance of Mineserver using the specified arguments.

        :param instance_id:
        :param memory_allocation:
        """

        self.instance_id = instance_id
        self.memory_allocation = memory_allocation

    def manage_server(self, client) -> str:
        """
        Gets IP Address for return to webpage otherwise boots server

        :return:
        """
        returnString = 'ERROR'

        instanceIds = [self.instance_id]
        response = client.describe_instances(InstanceIds=instanceIds)
        reservations = response['Reservations']
        reservation = reservations[0]

        instances = reservation['Instances']

        logger.info("\nSERVER INSTANCES\n")
        logger.info(instances)
        logger.info("\n")
        if len(instances) > 0:
            instance = instances[0]
            state = instance['State']
            stateName = state['Name']

            if (stateName == 'stopped') or (stateName == 'shutting-down'):
                # SETUP MULTIPROCESSING HERE INSTEAD OF REDIS
                returnString = self.start_server(client)
            elif stateName == 'running':
                returnString = 'IP: ' + instance['PublicIpAddress']
            else:
                returnString = 'ERROR'
        return returnString

    def start_server(self, client) -> str:
        """
        Starts the specified AWS Instance from the configuration.
        Gets proper variables to attempt to instantiate EC2 instance and start minecraft server.

        :param client:
        :return:
        """

        instance = None
        instanceIds = [self.instance_id]
        response = client.start_instances(InstanceIds=instanceIds)

        stateCode = 0

        while not (stateCode == 16):
            time.sleep(3)

            logger.info('\nAWS EC2 START RESPONSE\n')
            logger.info(str(response))
            logger.info('\n')

            response = client.describe_instances(InstanceIds=instanceIds)
            reservations = response['Reservations']
            reservation = reservations[0]

            instances = reservation['Instances']
            instance = instances[0]

            state = instance['State']
            stateCode = state['Code']

            logger.info("\nSERVER INSTANCES\n")
            logger.info(instances)
            logger.info("\n")

        if instance is None:
            returnString = 'ERROR'
        else:
            ipAddress = instance['PublicIpAddress']
            returnString = 'Server is starting, this may take a few minutes.\nIP: ' + ipAddress
            # SETUP MULTIPROCESSING HERE INSTEAD OF REDIS
            p = Process(target=self.server_wait_ok, args=(ipAddress, client))
            p.start()

        return returnString

    # Waits for the server to reach a valid state so that commands can be executed on the server
    def server_wait_ok(self, instanceIp, client):
        checksPassed = False
        status = 'initializing'
        instanceIds = [self.instance_id]

        while (not checksPassed) and (status == 'initializing'):
            statusCheckResponse = client.describe_instance_status(InstanceIds=instanceIds)
            instanceStatuses = statusCheckResponse['InstanceStatuses']
            instanceStatus = instanceStatuses[0]
            instanceStatus = instanceStatus['InstanceStatus']
            status = instanceStatus['Status']
            checksPassed = status == 'ok'
            time.sleep(5)

        if checksPassed:
            self.init_server_commands(instanceIp)
        else:
            logger.error('An error has occurred booting the server')

    # SSH connects to server and executes command to boot minecraft server
    def init_server_commands(self, instanceIp):
        # Connect/ssh to an instance
        try:
            # Here 'ubuntu' is user name and 'instance_ip' is public IP of EC2
            sshClient.connect(hostname=instanceIp, username="ubuntu", pkey=key)

            # Execute a command(cmd) after connecting/ssh to an instance
            stdin, stdout, stderr = sshClient.exec_command(
                "screen -dmS minecraft bash -c 'sudo java " + self.memory_allocation + "-jar server.jar nogui'")
            logger.info("COMMAND EXECUTED")
            # close the client connection once the job is done
            sshClient.close()

        except:
            logger.error('Error running server commands')


def create_instance():
    client = boto3.resource(
        'ec2',
        aws_access_key_id=aws_config['access_key'],
        aws_secret_access_key=aws_config['secret_key'],
        region_name=aws_config['ec2_region']
    )
    response = client.create_instances(ImageId=aws_config['ec2_amis'][0],
                                       InstanceType=aws_config['ec2_instancetype'],
                                       KeyName=aws_config['ec2_keypair'],
                                       MaxCount=1,
                                       MinCount=1,
                                       SecurityGroups=aws_config['ec2_secgroups'])

    logger.info("INSTANCE CREATED")
    logger.info("INSTANCE ID: " + response[0].id)


# Main endpoint for loading the webpage
@app.route('/')
def loadIndex():
    return render_template('index.html')


@app.route('/initServerMC', methods=['POST'])
def initServerMC():
    inputPass = request.form['pass']

    message = "Password Incorrect!"

    if inputPass == web_client_config['server_password']:
        # Instantiate server here or return ip address if already running
        client = boto3.client(
            'ec2',
            aws_access_key_id=aws_config['access_key'],
            aws_secret_access_key=aws_config['secret_key'],
            region_name=aws_config['ec2_region']
        )
        message = mineserver.manage_server(client)

    logger.info(message)
    return render_template('index.html', ipMessage=message)


if __name__ == "__main__":
    # Initialize
    args = _argparser()
    _setup_log(log_path=args.log)

    # Load the configuration
    logger = logging.getLogger('Init')
    logger.debug("Loading the configs..")
    config = Configuration(config_src=args.config_file)
    aws_config = config.get_aws_configs()[0]
    mineserver_config = config.get_mineserver_configs()[0]
    web_client_config = config.get_web_client_configs()[0]

    if args.run_mode == 'run_flask':
        logger = logging.getLogger('Flask App')
        # Setup paraminko ssh information
        logger.debug("Setting up paraminko ssh information")
        key = paramiko.RSAKey.from_private_key_file(mineserver_config['ssh_key_file_path'])
        sshClient = paramiko.SSHClient()
        sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Initialize the Mineserver class
        logger.debug("Initializing the Mineserver class..")
        mineserver = Mineserver(instance_id=aws_config['instance_id'],
                                memory_allocation=mineserver_config['memory_allocation'])
        # Start the Flask app
        logger.debug("Starting the flask app..")
        app.run()
    elif args.run_mode == 'create_instance':
        logger = logging.getLogger('Create Instance')
        create_instance()
    else:
        raise argparse.ArgumentTypeError('Invalid run mode specified!')
