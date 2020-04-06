import sys
import os
import boto3
sys.path.append(os.path.dirname(os.path.abspath("configuration.py")))
from configuration import Config

if not len(sys.argv) == 3:
    print("Usage: createInstance.py <AWS access key> <AWS secret key>")
    sys.exit()

ACCESS_KEY = sys.argv[1]
SECRET_KEY = sys.argv[2]

client = boto3.resource(
            'ec2',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=Config.ec2_region
        )
response = client.create_instances(ImageId = Config.ec2_amis[0],
    InstanceType = Config.ec2_instancetype, 
    KeyName = Config.ec2_keypair,
    MaxCount = 1,
    MinCount = 1,
    SecurityGroups = Config.ec2_secgroups)

print("INSTANCE CREATED")
print("INSTANCE ID: " + response[0].id)