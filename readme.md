# On Demand Minecraft Server
Using a Python Flask application and AWS, this repository launches an AWS EC2 Instance to host a Minecraft server upon request from users through the web application. The server will automatically shut down after the server has crashed or is empty for 15 minutes. This makes server hosting for small communities very inexpensive. For up to 20 players you can expect $0.02 per hour the server runs. The largest benefit of this system is that the server bill diminishes if your community decides to take a break from the game, and will be ready to pick back up when you want to play again. No subscriptions are required.

Note that this configuration will likely require familiarity with programming, SSH, and the command line.


# Web Application Setup

In this step the project will get linked to Heroku's free hosting. This part of the application provides a rudimentary UI and Web URL for users to start the server. Before we deploy the webapp, we will configure it with information about the AWS instance in the next section.

 1. Create or have access to a Heroku account.
 2. Install and setup the **Heroku CLI** onto your computer. [https://devcenter.heroku.com/articles/heroku-cli#download-and-install](https://devcenter.heroku.com/articles/heroku-cli#download-and-install)
 3. In the command line for the directory of this project, type:
	 <code>heroku create YourProjectNameHere</code>

 Now the webapp should be visible in the Heroku dashboard, but it is not deployed yet.

# AWS Setup
This step will properly configure your AWS account and configuration.py file so that an instance can be created via the createInstance.py script. We will also set configuration variables for the heroku webapp so that it knows how to access the instance.

 1. Create or access an **AWS Account**. Under the **User Dropdown** in the    **Toolbar**, select **Security Credentials**, then **Access Keys**, and finally **Create New Access Key**. Download this file, open it, and make note of the values of **AWSAccessKeyId** and **AWSSecretKey**. Later, we will supply these to the instance creation script. For now, we need to allow the heroku app to access them by setting them as configuration variables.

	<code>
	heroku config:set ACCESS_KEY=Your-access-key-here
	</code>
	<code>
	heroku config:set SECRET_KEY=Your-secret-key-here
	</code>

 3. Navigate to the **EC2 Dashboard** under the **Services Dropdown** and select **Security Groups** in the sidebar. Select **Create Security Group**, input **minecraft** for the **Security group name**. Create **Inbound Rules** for the following:
	 - Type: **SSH** Protocol: **TCP** Port Range: **22** Source: **Anywhere**
	 - Type: **Custom TCP Rule** Protocol: **TCP** Port Range: **25565** Source: **Anywhere**
	 - Type: **Custom UDP Rule** Protocol: **UDP** Port Range: **25565** Source: **Anywhere**
	 
	 In **configuration.py** in the root directory, set **ec2_secgroups** to the name of the security group.
	 
	 <code>ec2_secgroups =  ['YourGroupNameHere']</code>

3. Under the **EC2 Dashboard** navigate to **Key Pairs** in the sidebar. Select **Create Key Pair**, provide a name and create. Move the file that is downloaded into the root directory of the project (or somewhere else safe) so that you can use it to SSH into the instance later. In **configuration.py** in the root directory, set **ec2_keypair** to the name entered. Also configure the heroku webapp with the contents of the key file.

	Inside **configuration.py**:
		<code>ec2_keypair =  'YourKeyPairName'</code>
	
	To configure heroku, it is easiest to copy-paste the contents of the file via the [heroku dashboard](https://dashboard.heroku.com). Select your app, go to **Settings**, scroll down to **Config Vars**, and add a new one with the name `SSH_KEY` and the value as the contents of the private key file you downloaded.

4. This step is concerned with creating the AWS instance. View [https://docs.aws.amazon.com/general/latest/gr/rande.html](https://docs.aws.amazon.com/general/latest/gr/rande.html) (Or google AWS Regions), and copy the  **Region** column for the **Region Name** of where you wish to host your server. In **configuration.py** of the root directory, set the **ec2_region** variable to the copied value. Also configure the heroku app.

	Inside **configuration.py**:
		<code>ec2_region =  "Your-Region-Here"</code>

	On the command line:
		<code>heroku config:set EC2_REGION=Your-Region-Here</code>

5. Navigate to [https://aws.amazon.com/ec2/instance-types/](https://aws.amazon.com/ec2/instance-types/) and select one of the T3 types (with the memory and CPU you desire, I recommend 10 players/GB). Copy the value in the **Model** column. I've configured mine to use **t3.small**. In **configuration.py** of the root directory, set the **ec2_instancetype** variable to the copied value.

	<code>ec2_instancetype =  't3.yourSizeHere'</code>

6. Then we must select an image for the instance to boot. Navigate to [https://cloud-images.ubuntu.com/locator/ec2/](https://cloud-images.ubuntu.com/locator/ec2/), in the filter at the bottom of the screen, select your region of choice under **Zone**, pick any LTS (Latest Stable) under **Version**, under **Arch** select **amd64**, and **hvm:ebs** under **Instance Type**. Select one of the images available and copy the **AMI-ID**. In **configuration.py** of the root directory, set the **ec2_amis** variable to the copied value.

	<code>ec2_amis =  ['ami-YourImageIdHere']</code>

7. At this point you should have the necessary configuration to create a new instance through the **createInstance.py** script in the **root** folder. Open a command line in the utilityScripts directory of the project, and execute:

	<code>pip install -r requirements.txt</code>
	
	After successful installation of dependencies execute the script with the AWS access key and secret key as arguments from step 1.

	<code>python utilityScripts/createInstance.py <Your access key here> <Your secret key here></code>

	Copy the **Instance ID** that is output into the terminal. Tell the heroku webapp that this is your instance id.

	<code>heroku config:set INSTANCE_ID=i-yourInstanceIdHere</code>


# Web Application Deployment

Now we have created the ec2 instance and configured the webapp configuration variables, we are almost ready to deploy the webapp.

Before deployment it will be important to set the password for the server to start. Set the **SERVER_PASSWORD** config variable to the password of your choosing.

   <code>heroku config:set SERVER_PASSWORD="YourPasswordHere"</code>
 
1. Once this new project has been created, it is time to push the project to Heroku.
	<code>git push heroku master</code>
2. The URL to your hosted site should be: YourProjectNameHere.herokuapp.com
3. Access your site and launch/access your server!

# AWS Instance Configuration
This step will configure the AWS Linux server to run the minecraft server. It will include SSH connecting to the server, gaining admin privileges, installing java, directory setup, moving shell scripts onto the server, and making a CRON job for these shell scripts. Note that this step will include both an SSH client and a File Transfer client (such as FileZilla) on your PC.
1. The first step will be to get SSH into the server instance. Using the key downloaded from AWS in the section above, add this key to PuTTY or simply access it through command line. The IP address can be obtained by entering the server password on the site, or through the EC2 Dashboard, selecting the iPV4 address from the corresponding instanceID in your configuration file. For MacOS and Linux systems

	<code>ssh -i pathToYourKeyFileHere ubuntu@IPAddress</code>

2. Make the ubuntu user admin if it isn't already with:
 
	<code>adduser ubuntu sudo</code>

3. The next step will be to install JavaJDK onto your system. For newer versions you may enter:
	<code>sudo apt install openjdk-11-jdk-headless</code>
	If this doesn't work you can use <code>sudo apt list</code> and search through these packages for an alternative java version.

4. Open up an FTP client such as FileZilla and connect to the same address as the same user with the same IP address. Drag all files from the **instanceSetup** folder from this repository, into the root directory of the current user (probably **ubuntu**, for the purposes of these commands I will be using **ubuntu**, but feel free to replace with your own user if appropriate).

5.  Download the desired Minecraft server version from [https://www.minecraft.net/en-us/download/server/](https://www.minecraft.net/en-us/download/server/), rename it **server.jar** and drag it into the root directory of the user using FileZilla.

6. Using the FTP client, create a new folder in the root directory of the current user called **screens**  
OR  
In the SSH client, create a folder in the current directory with the command:
	<code>sudo mkdir screens</code>
7. Then execute the following command:
   <code>sudo chmod 700 /home/ubuntu</code>
8. Then execute the next command:
  <code>export SCREENDIR=/home/ubuntu/screens</code>
9. Then execute the command:
  <code>sudo crontab /home/ubuntu/crontab -u ubuntu</code>

	Feel free to close the server through the AWS console or execute the command:
	<code>sudo /sbin/shutdown -P +1</code>

At this point you may restart the server from the Web Application using the password you configured. You should then be able to play!

# Additional Remarks
## Minecraft Memory Configuration
The server startup command does not specify memory constraints by default, but is available to be specified in Configuration.py. In the event that you configure this from an empty string, **the trailing space is required** as in the example below. Traditional minecraft server flags apply for this configuration.
<code>MEMORY_ALLOCATION='-Xmx1024M -Xms1024M '</code>
## UI Configuration
The title and header for the site can be changed in **/templates/index.html**. Feel free to add any more content or styling to the site, though be careful not to change any form, input, button, or script elements in the template.

## Server Maintenance
Maintaining the server is fairly straightforward and is done primarily through FileZilla. Updating the server file can be done by downloading the new server file, renaming it to **server.jar** and replacing the old file on the server. The world file can be backed up to your PC manually though there is no automated process at this time.
