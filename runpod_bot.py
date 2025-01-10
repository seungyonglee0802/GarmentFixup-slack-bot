import os
from dotenv import load_dotenv
import time
import subprocess
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List

load_dotenv()

# Initialize the Slack app
app = App(token=os.environ["RUNPOD_SLACK_BOT_TOKEN"])

@dataclass
class PodCreationConfig:
    name: str
    image_name: str
    network_volume_id: str
    volume_path: str
    gpu_count: int
    gpu_type: str
    ssh_public_keys: List[str]
    ports: str = "22/tcp"
    secure_cloud: bool = True
    container_disk_size: int = 100
    volume_size: int = 100
    vcpus: int = 16

@dataclass
class PodConfig:
    name: str
    ssh_user: str
    ssh_key_path: str
    process_name: str
    run_script: str
    log_file: str
    pod_id: Optional[str] = None
    creation_config: Optional[PodCreationConfig] = None

# Configuration for multiple instances
PODS = {
    "body": PodConfig(
        name="body-part-fixer",
        ssh_user="root",
        ssh_key_path="/home/sylee/.ssh/runpod_4090_id_ed25519",
        process_name="app.py",
        run_script="/workspace/run.sh",
        log_file="~/app.log",
        creation_config=PodCreationConfig(
            name="body-part-fixer",
            image_name="runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
            network_volume_id="gnjw8sm1l4",
            volume_path="/workspace",
            gpu_count=1,
            gpu_type="NVIDIA GeForce RTX 4090",
            ssh_public_keys=[
                "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAAQh/JvlmW9b9Z7hIxVsiJzVnLORE06fx776Sms6+VO soohyeok@nxn.ai",
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDZEYRhLCAK6ea+wPFgRoKhtRZESIvpW4wU0xwPntGWvTcs+ub5eSpQomWEFHfccWYtTBI3T8TgOBcrNX6yA+4gOGwzFStKAvNqTV21HC7WlWIAt5Yx9tGC8iwPlvHGwNlqGOfoMll6WBnsxWGA/jvecr6jRx7e71HoMy3SljGWdo/UWtrX+dYQyh6enGIpZ5rPGKOgeztTH6ZjMfnvJml93pNh7b5aWEU0FwVy+fqiIITqH4u+IVt27Enoc2b2p0XSgKlr0pJjF4iYc473NZYsV0KpvfZT+DLqOg7L/C14ZLr8HeXFg+0+Ong6ET89o2Reh8xkPt+TRovnsOdajPqr RunPod-Key-Go",
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCt8MMuB/uLEQIj9p/P563hAU5oIlzw03nOoUFTjYbo6Kk6Gt7yBVDZD5xqWdLWcyw4OSefwCFeiWE+s6fcP4JUns1e8/P3yUYtgBWtj9YTQXn6JgY4IZ/VyKWkoEWmTYL/AS1kxAD9r9Hpmb5U/oRhdOokmGvLhHabj8InsNvHEKtJcleXcQXz0HV+jeq4rqmgIi46bucpB3eOYV+4rlehKIi52ClsAWbGEQGHCAg0XKP3UtWjYiR7NYP00kdS+EuThc1PMaZChrceP/BHfxDkC2XQezU+0WOAMiZQ/NyRnJ6NLaPd9viE27ZMxbQeR3vmEsUn1UptSSe3h3ET1rkT RunPod-Key-Go"
            ],
            volume_size=100,
        )
    ),
    "comfy": PodConfig(
        name="comfy-ui",
        ssh_user="root",
        ssh_key_path="/home/sylee/.ssh/runpod_4090_id_ed25519",
        process_name="main.py",
        run_script="/workspace/run.sh",
        log_file="~/app.log",
        creation_config=PodCreationConfig(
            name="comfy-ui",
            image_name="runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
            network_volume_id="rhpkf9qeak",
            volume_path="/workspace",
            gpu_count=1,
            gpu_type="NVIDIA GeForce RTX 4090",
            ssh_public_keys=[
                "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAAQh/JvlmW9b9Z7hIxVsiJzVnLORE06fx776Sms6+VO soohyeok@nxn.ai",
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDZEYRhLCAK6ea+wPFgRoKhtRZESIvpW4wU0xwPntGWvTcs+ub5eSpQomWEFHfccWYtTBI3T8TgOBcrNX6yA+4gOGwzFStKAvNqTV21HC7WlWIAt5Yx9tGC8iwPlvHGwNlqGOfoMll6WBnsxWGA/jvecr6jRx7e71HoMy3SljGWdo/UWtrX+dYQyh6enGIpZ5rPGKOgeztTH6ZjMfnvJml93pNh7b5aWEU0FwVy+fqiIITqH4u+IVt27Enoc2b2p0XSgKlr0pJjF4iYc473NZYsV0KpvfZT+DLqOg7L/C14ZLr8HeXFg+0+Ong6ET89o2Reh8xkPt+TRovnsOdajPqr RunPod-Key-Go",
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCt8MMuB/uLEQIj9p/P563hAU5oIlzw03nOoUFTjYbo6Kk6Gt7yBVDZD5xqWdLWcyw4OSefwCFeiWE+s6fcP4JUns1e8/P3yUYtgBWtj9YTQXn6JgY4IZ/VyKWkoEWmTYL/AS1kxAD9r9Hpmb5U/oRhdOokmGvLhHabj8InsNvHEKtJcleXcQXz0HV+jeq4rqmgIi46bucpB3eOYV+4rlehKIi52ClsAWbGEQGHCAg0XKP3UtWjYiR7NYP00kdS+EuThc1PMaZChrceP/BHfxDkC2XQezU+0WOAMiZQ/NyRnJ6NLaPd9viE27ZMxbQeR3vmEsUn1UptSSe3h3ET1rkT RunPod-Key-Go"
            ],
            volume_size=500,
            ports="22/tcp,8188/http,8288/http,8888/http",
        )
    )
}

class RunPodManager:
    def __init__(self, pod_config: PodConfig):
        self.config = pod_config

    def create_pod(self) -> Optional[str]:
        """Create a new RunPod instance"""
        
        if not self.config.creation_config:
            raise Exception("No creation configuration provided")

        try:
            # Combine all SSH public keys into a single string
            public_keys = '\\n'.join(self.config.creation_config.ssh_public_keys)
                        
            create_command = [
                'runpodctl', 'create', 'pod',
                '--name', self.config.creation_config.name,
                '--imageName', self.config.creation_config.image_name,
                '--ports', self.config.creation_config.ports,
                '--networkVolumeId', self.config.creation_config.network_volume_id,
                '--volumePath', self.config.creation_config.volume_path,
                '--gpuCount', str(self.config.creation_config.gpu_count),
                '--gpuType', self.config.creation_config.gpu_type,
                '--containerDiskSize', str(self.config.creation_config.container_disk_size),
                '--volumeSize', str(self.config.creation_config.volume_size),
                '--vcpu', str(self.config.creation_config.vcpus),
                '--env', f'PUBLIC_KEY={public_keys}'
            ]

            if self.config.creation_config.secure_cloud:
                create_command.append('--secureCloud')

            result = subprocess.run(
                create_command,
                capture_output=True,
                text=True,
                check=True
            )

            # Extract pod ID from output (e.g., 'pod "3poqikuwhnr5qm" created for $0.690 / hr')
            import re
            match = re.search(r'pod "([^"]+)" created', result.stdout)
            if match:
                pod_id = match.group(1)
                self.config.pod_id = pod_id
                return pod_id
            raise Exception("Failed to extract pod ID from creation output")

        except subprocess.CalledProcessError as e:
            print(f"CalledProcessError occurred: {str(e)}")
            raise Exception(f"Failed to create RunPod instance: {e.stderr}")
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            raise

    def get_pod_ssh_details(self) -> Optional[Tuple[str, str]]:
        """Get SSH connection details from runpodctl"""
        if not self.config.pod_id:
            raise Exception("No pod ID available")

        try:
            result = subprocess.run(
                ['runpodctl', 'get', 'pod', '-a', self.config.pod_id],
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                raise Exception("No pod data found")
                
            pod_data = lines[-1].split()
            ports_section = None
            for field in pod_data:
                if '->22' in field:
                    ports_section = field
                    break
                    
            if not ports_section:
                return None
                
            ip_port = ports_section.split('->')[0]
            ip, port = ip_port.split(':')
            ip = ip.split(',')[-1].strip()
            return ip, port

        except Exception as e:
            raise Exception(f"Failed to get pod details: {str(e)}")

    def ssh_connect_and_run(self, command: str) -> Tuple[int, str, str]:
        """Execute a command on the remote instance via SSH"""
        try:
            ip, port = self.get_pod_ssh_details()
            
            ssh_command = [
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-p', port,
                '-i', self.config.ssh_key_path,
                f'{self.config.ssh_user}@{ip}',
                command
            ]
            
            result = subprocess.run(
                ssh_command,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return 1, '', str(e)

    def start_instance(self) -> bool:
        """Start the RunPod instance"""
        if not self.config.pod_id:
            raise Exception("No pod ID available")

        try:
            subprocess.run(
                ['runpodctl', 'start', 'pod', self.config.pod_id],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to start RunPod instance: {e.stderr}")

    def stop_instance(self) -> bool:
        """Stop the RunPod instance"""
        if not self.config.pod_id:
            raise Exception("No pod ID available")

        try:
            subprocess.run(
                ['runpodctl', 'stop', 'pod', self.config.pod_id],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to stop RunPod instance: {e.stderr}")

    def remove_instance(self) -> bool:
        """Remove the RunPod instance"""
        if not self.config.pod_id:
            raise Exception("No pod ID available")

        try:
            subprocess.run(
                ['runpodctl', 'remove', 'pod', self.config.pod_id],
                capture_output=True,
                text=True,
                check=True
            )
            self.config.pod_id = None
            return True

        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to remove RunPod instance: {e.stderr}")

    def check_instance_status(self) -> bool:
        """Check if the instance is running"""
        return self.get_pod_ssh_details() is not None

    def check_process_status(self) -> bool:
        """Check if the process is running"""
        exit_status, output, _ = self.ssh_connect_and_run(f'pgrep -f {self.config.process_name}')
        return exit_status == 0 and bool(output)

    def get_process_url(self) -> Optional[str]:
        """Get the URL for the running process. Handles both Gradio and proxy URLs."""
        # First try to find a Gradio URL
        exit_status, output, _ = self.ssh_connect_and_run(
            f"grep -oP 'https://[a-z0-9]+\.gradio\.live' {self.config.log_file}"
        )
        
        if exit_status == 0 and output:
            return output.splitlines()[-1]
        
        # If no Gradio URL found, look for proxy port
        exit_status, output, _ = self.ssh_connect_and_run(
            f"grep -oP 'To see the GUI go to: http://(?:[0-9.]+|\[::\]):(\d+)' {self.config.log_file}"
        )
        
        if exit_status == 0 and output:
            # Extract port from the last matching line
            import re
            last_line = output.splitlines()[-1]
            match = re.search(r':(\d+)$', last_line)
            if match and self.config.pod_id:
                port = match.group(1)
                return f"https://{self.config.pod_id}-{port}.proxy.runpod.net"
        
        return None

    def start_process(self) -> Tuple[int, str, str]:
        """Start the process on the instance"""
        return self.ssh_connect_and_run(f'bash {self.config.run_script}')

def create_create_command(instance_name: str):
    """Create a pod creation command for a specific instance"""
    def create_handler(ack, say, command):
        ack()
        pod_manager = RunPodManager(PODS[instance_name])
        
        try:
            say(f"Creating new pod for {instance_name}...")
            pod_id = pod_manager.create_pod()
            say(f"Successfully created pod for {instance_name} with ID: {pod_id}")
            
        except Exception as e:
            say(f"Error creating pod for {instance_name}: {str(e)}")
    
    return create_handler

def create_launch_command(instance_name: str):
    """Create a launch command for a specific instance"""
    def launch_handler(ack, say, command):
        ack()
        pod_manager = RunPodManager(PODS[instance_name])
        
        try:
            if not pod_manager.config.pod_id:
                say(f"No pod ID available for {instance_name}. Please create the pod first using /{instance_name}_create")
                return

            if pod_manager.check_instance_status():
                say(f"{instance_name} is already running. Checking process status...")
            else:
                say(f"{instance_name} is not running. Starting it now...")
                pod_manager.start_instance()
                say("Waiting for instance to be ready...")
                time.sleep(30)

            process_status = pod_manager.check_process_status()
            
            if not process_status:
                say(f"Process on {instance_name} is not running. Starting it now... (It may take up to 10 minutes)")
                exit_status, output, error = pod_manager.start_process()
                
                if exit_status != 0:
                    raise Exception(f"Failed to start process: {error}")
                
                time.sleep(30)
                
                for attempt in range(10):
                    url = pod_manager.get_process_url()
                    if url:
                        say(f"Process on {instance_name} is running. URL: {url}")
                        break
                    if attempt < 9:
                        time.sleep(60)
                else:
                    say(f"Could not retrieve the URL for {instance_name} after 10 attempts.")
            else:
                url = pod_manager.get_process_url()
                if url:
                    say(f"Process on {instance_name} is already running. URL: {url}")
                else:
                    say(f"Process on {instance_name} is running but couldn't retrieve the URL.")
                    
        except Exception as e:
            say(f"Error with {instance_name}: {str(e)}")
    
    return launch_handler

def create_status_command(instance_name: str):
    """Create a status check command for a specific instance"""
    def status_handler(ack, say, command):
        ack()
        pod_manager = RunPodManager(PODS[instance_name])
        
        try:
            if not pod_manager.config.pod_id:
                say(f"No pod ID available for {instance_name}. Please create the pod first using /{instance_name}_create")
                return

            instance_running = pod_manager.check_instance_status()
            if not instance_running:
                say(f"{instance_name} is not running. Use the launch command to start it.")
                return
            
            process_running = pod_manager.check_process_status()
            
            if process_running:
                url = pod_manager.get_process_url()
                say(f"{instance_name} status:\nInstance: Running\nProcess: Active\nURL: {url}")
            else:
                say(f"{instance_name} status:\nInstance: Running\nProcess: Not active")
        except Exception as e:
            say(f"Error checking {instance_name} status: {str(e)}")
    
    return status_handler

def create_stop_command(instance_name: str):
    """Create a stop command for a specific instance"""
    def stop_handler(ack, say, command):
        ack()
        pod_manager = RunPodManager(PODS[instance_name])
        
        try:
            if not pod_manager.config.pod_id:
                say(f"No pod ID available for {instance_name}. Please create the pod first using /{instance_name}_create")
                return

            if pod_manager.stop_instance():
                say(f"{instance_name} has been stopped successfully.")
        except Exception as e:
            say(f"Error stopping {instance_name}: {str(e)}")
    
    return stop_handler

def create_remove_command(instance_name: str):
    """Create a remove command for a specific instance"""
    def remove_handler(ack, say, command):
        ack()
        pod_manager = RunPodManager(PODS[instance_name])
        
        try:
            if not pod_manager.config.pod_id:
                say(f"No pod ID available for {instance_name}. Please create the pod first using /{instance_name}_create")
                return

            if pod_manager.remove_instance():
                say(f"{instance_name} has been removed successfully.")
        except Exception as e:
            say(f"Error removing {instance_name}: {str(e)}")
    
    return remove_handler

# Create combined launch command that handles creation and startup
def create_combined_launch_command(instance_name: str):
    """Create a command that handles both creation and launch for a specific instance"""
    def combined_launch_handler(ack, say, command):
        ack()
        pod_manager = RunPodManager(PODS[instance_name])
        
        try:
            # Check if pod exists and create if necessary
            if not pod_manager.config.pod_id:
                say(f"No existing pod found for {instance_name}. Creating new pod...")
                pod_id = pod_manager.create_pod()
                say(f"Successfully created pod with ID: {pod_id}")
                say("Waiting for pod to be ready...")
                time.sleep(30)  # Wait for pod to initialize

            # Continue with launch process
            if pod_manager.check_instance_status():
                say(f"{instance_name} is already running. Checking process status...")
            else:
                say(f"{instance_name} is not running. Starting it now...")
                pod_manager.start_instance()
                say("Waiting for instance to be ready...")
                time.sleep(30)

            process_status = pod_manager.check_process_status()
            
            if not process_status:
                say(f"Process on {instance_name} is not running. Starting it now... (It may take up to 10 minutes)")
                exit_status, output, error = pod_manager.start_process()
                
                if exit_status != 0:
                    raise Exception(f"Failed to start process: {error}")
                
                time.sleep(30)
                
                for attempt in range(10):
                    url = pod_manager.get_process_url()
                    if url:
                        say(f"Process on {instance_name} is running. URL: {url}")
                        break
                    if attempt < 9:
                        time.sleep(60)
                else:
                    say(f"Could not retrieve the URL for {instance_name} after 10 attempts.")
            else:
                url = pod_manager.get_process_url()
                if url:
                    say(f"Process on {instance_name} is already running. URL: {url}")
                else:
                    say(f"Process on {instance_name} is running but couldn't retrieve the URL.")
                    
        except Exception as e:
            say(f"Error with {instance_name}: {str(e)}")
    
    return combined_launch_handler

# Register commands for each instance
for instance_name in PODS.keys():
    app.command(f"/{instance_name}_start")(create_combined_launch_command(instance_name))
    app.command(f"/{instance_name}_status")(create_status_command(instance_name))
    app.command(f"/{instance_name}_stop")(create_remove_command(instance_name))

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["RUNPOD_SLACK_APP_TOKEN"])
    handler.start()