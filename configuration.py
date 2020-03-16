class Config:
    #AWS Information
    ACCESS_KEY = ''
    SECRET_KEY = ''
    INSTANCE_ID = ''
    ec2_region = ""
    ec2_amis = ['']
    ec2_keypair = ''
    ec2_secgroups = [''] #ID Not Name
    ec2_instancetype = ''

    #SSH Key Path
    SSH_KEY_FILE_PATH = ''

    #Server Memory Size
    #This is default to no memory specification but can be: '-Xmx1024M -Xms1024M ' (KEEP TRAILING SPACE)
    MEMORY_ALLOCATION='' 