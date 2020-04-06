from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from multiprocessing import Process
import json
import boto3
import time
import paramiko
import os
import io

app = Flask(__name__)
CORS(app)

# Paraminko ssh information
key_string = os.getenv('SSH_KEY').replace('\\n', '\n')
key = paramiko.RSAKey.from_private_key(io.StringIO(key_string))
sshClient = paramiko.SSHClient()
sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def serverWaitOk(instanceIp, client):
    """Waits for the server to reach a valid state so that commands can be executed on the server"""
    checksPassed = False
    status = 'initializing'
    instanceIds = [os.getenv('INSTANCE_ID')]

    while (not checksPassed) and (status == 'initializing'):
        statusCheckResponse = client.describe_instance_status(
            InstanceIds=instanceIds)
        instanceStatuses = statusCheckResponse['InstanceStatuses']
        instanceStatus = instanceStatuses[0]
        instanceStatus = instanceStatus['InstanceStatus']
        status = instanceStatus['Status']
        checksPassed = status == 'ok'
        time.sleep(5)

    if checksPassed:
        initServerCommands(instanceIp)
    else:
        print('An error has occurred booting the server')


def initServerCommands(instanceIp):
    """SSH connects to server and executes command to boot minecraft server"""
    # Connect/ssh to an instance
    try:
        # Here 'ubuntu' is user name and 'instance_ip' is public IP of EC2
        sshClient.connect(hostname=instanceIp, username="ubuntu", pkey=key)

        # Execute a command(cmd) after connecting/ssh to an instance
        stdin, stdout, stderr = sshClient.exec_command(
            "screen -dmS minecraft bash -c 'sudo java " + os.getenv('MEMORY_ALLOCATION', '') + "-jar server.jar nogui'")
        print("COMMAND EXECUTED")
        # close the client connection once the job is done
        sshClient.close()

    except Exception as err:
        print('Error running server commands')
        print(err)


@app.route('/')
def loadIndex():
    """Main endpoint for loading the webpage"""
    return render_template('index.html')


@app.route('/initServerMC', methods=['POST'])
def initServerMC():
    inputPass = request.form['pass']
    returnData = {}

    message = "Password Incorrect!"

    if inputPass == os.getenv('SERVER_PASSWORD'):
        # Instantiate server here or return ip address if already running
        client = boto3.client(
            'ec2',
            aws_access_key_id=os.getenv('ACCESS_KEY'),
            aws_secret_access_key=os.getenv('SECRET_KEY'),
            region_name=os.getenv('EC2_REGION')
        )
        message = manageServer(client)

    print(message)
    return render_template('index.html', ipMessage=message)


def manageServer(client):
    """Gets IP Address for return to webpage otherwise boots server"""
    returnString = 'ERROR'

    instanceIds = [os.getenv('INSTANCE_ID')]
    response = client.describe_instances(InstanceIds=instanceIds)
    reservations = response['Reservations']
    reservation = reservations[0]

    instances = reservation['Instances']

    print("\nSERVER INSTANCES\n")
    print(instances)
    print("\n")
    if len(instances) > 0:
        instance = instances[0]
        state = instance['State']
        stateName = state['Name']

        if (stateName == 'stopped') or (stateName == 'shutting-down'):
            # SETUP MULTIPROCESSING HERE INSTEAD OF REDIS
            returnString = startServer(client)
        elif stateName == 'running':
            returnString = 'IP: ' + instance['PublicIpAddress']
        else:
            returnString = 'ERROR'
    return returnString

def startServer(client):
    """Starts the specified AWS Instance from the configuration"""
    # Gets proper variables to attempt to instantiate EC2 instance and start minecraft server
    returnString = 'ERROR'
    instanceIds = [os.getenv('INSTANCE_ID')]
    response = client.start_instances(InstanceIds=instanceIds)

    stateCode = 0

    while not (stateCode == 16):
        time.sleep(3)

        print('\nAWS EC2 START RESPONSE\n')
        print(str(response))
        print('\n')

        response = client.describe_instances(InstanceIds=instanceIds)
        reservations = response['Reservations']
        reservation = reservations[0]

        instances = reservation['Instances']
        instance = instances[0]

        state = instance['State']
        stateCode = state['Code']

        print("\nSERVER INSTANCES\n")
        print(instances)
        print("\n")

    ipAddress = instance['PublicIpAddress']
    returnString = 'Server is starting, this may take a few minutes.\nIP: ' + ipAddress
    # SETUP MULTIPROCESSING HERE INSTEAD OF REDIS
    p = Process(target=serverWaitOk, args=(ipAddress, client))
    p.start()
    return returnString


if __name__ == "__main__":
    app.run()
