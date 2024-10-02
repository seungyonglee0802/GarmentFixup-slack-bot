import os
from dotenv import load_dotenv
import time
import paramiko
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import boto3

load_dotenv()

# Initialize the Slack app
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Initialize AWS EC2 client
ec2 = boto3.client('ec2', 
                   region_name=os.environ['AWS_REGION_NAME'],
                   aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                   aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])

# SSH credentials
SSH_USERNAME = "ubuntu"  # or the appropriate username for your instance
SSH_KEY_PATH = "/home/sylee/.ssh/aws.pem"

def get_instance_ip(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response['Reservations'][0]['Instances'][0]['PublicIpAddress']

def wait_for_instance(instance_id):
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])

def ssh_connect_and_run(ip_address, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(ip_address, username=SSH_USERNAME, key_filename=SSH_KEY_PATH)
        
        stdin, stdout, stderr = ssh.exec_command(command)
        
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        return exit_status, output, error
    finally:
        ssh.close()

def check_process_status(ip_address):
    exit_status, output, error = ssh_connect_and_run(ip_address, 'pgrep -f magicfu_gradio.py')
    if exit_status == 0 and output:
        return True
    elif exit_status == 1 and not output:
        return False
    else:
        raise Exception(f"Unexpected result from pgrep: status={exit_status}, output='{output}', error='{error}'")

def get_process_url(ip_address):
    exit_status, output, error = ssh_connect_and_run(ip_address, "grep -oP 'https://[a-z0-9]+\.gradio\.live' ~/fixup.log")
    if exit_status == 0 and output:
        return output
    else:
        return None

@app.command("/launch")
def start_instance(ack, say, command):
    ack()
    
    instance_id = os.environ["AWS_INSTANCE_ID"]
    
    try:
        # Check instance state
        response = ec2.describe_instances(InstanceIds=[instance_id])
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        
        if state != 'running':
            # Start the EC2 instance if it's not running
            ec2.start_instances(InstanceIds=[instance_id], DryRun=False)
            say("Starting EC2 instance. Please wait...")
            wait_for_instance(instance_id)
            time.sleep(60)  # Wait for services to start
        
        ip_address = get_instance_ip(instance_id)
        
        if not check_process_status(ip_address):
            say("GarmentFixup process is not running. Starting it now...")
            exit_status, output, error = ssh_connect_and_run(ip_address, 'bash run_garment_fixup.sh')
            if exit_status != 0:
                raise Exception(f"Failed to start GarmentFixup process: {error}")
            time.sleep(20)  # Wait for the process to start
        
        url = get_process_url(ip_address)
        if url:
            say(f"GarmentFixup process is running. Here's the URL: {url}")
        else:
            say("GarmentFixup process started, but couldn't retrieve the URL. Please check the instance.")
        
    except Exception as e:
        say(f"Error: {str(e)}")

@app.command("/check_status")
def check_status(ack, say, command):
    ack()
    
    instance_id = os.environ["AWS_INSTANCE_ID"]
    
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        
        if state == 'running':
            ip_address = get_instance_ip(instance_id)
            process_running = check_process_status(ip_address)
            
            if process_running:
                url = get_process_url(ip_address)
                say(f"EC2 instance is running (IP: {ip_address}).\nGarmentFixup process is active.\nURL: {url}")
            else:
                say(f"EC2 instance is running (IP: {ip_address}), but the GarmentFixup process is not active. Use /launch to start it.")
        else:
            say(f"The EC2 instance is currently {state}. Use /launch to start it and run the GarmentFixup process.")
    except Exception as e:
        say(f"Error checking status: {str(e)}")

@app.command("/quit")
def stop_instance(ack, say, command):
    ack()
    
    instance_id = os.environ["AWS_INSTANCE_ID"]
    
    try:
        # Stop the EC2 instance
        ec2.stop_instances(InstanceIds=[instance_id], DryRun=False)
        say("Stopping EC2 instance. Please wait...")
        
        # Wait for the instance to stop
        waiter = ec2.get_waiter('instance_stopped')
        waiter.wait(InstanceIds=[instance_id])
        
        say("EC2 instance has been stopped successfully.")
    except Exception as e:
        say(f"Error stopping instance: {str(e)}")

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()