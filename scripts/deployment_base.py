#!/usr/bin/env python3.6
import os
import sys
import subprocess
import shutil
import re
import logging
from distutils import dir_util
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.append('./')
from modules import setup

"""This is the Deployment Base Class which contains commonly used methods"""


class DeploymentBase(object):
    def __init__(self):
        class_name = self.__class__.__name__
        deployment_type = class_name.lower()

        # Configure logger
        logging.basicConfig(filename=f"{deployment_type}.log",
                            format='%(asctime)s [%(levelname)s]: %(message)s')

        self.logger = logging.getLogger(deployment_type)

        # Setting threshold level
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("-" * 100)
        self.logger.info(f"{class_name} started")

        """Get some config from the setup.py file"""
        required_fields = ("gcr_hostname", "gcp_project", "admin", "email_address", "email_password")

        for required_field in required_fields:
            if not setup.config[required_field]:
                raise Exception(f"{required_field} is empty in setup.py")

        self.version = setup.config["version"]
        self.gcr_hostname = setup.config["gcr_hostname"]
        self.gcp_project = setup.config["gcp_project"]
        self.admin = setup.config["admin"]
        self.email_address = setup.config["email_address"]
        self.email_password = setup.config["email_password"]

        """Log in to SMTP server at the beginning of the process, so an error isn't only received
        once the deployment is complete that the email authentication failed"""
        try:
            self.smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
            self.smtp_server.starttls()
            self.smtp_server.login(self.email_address, self.email_password)
        except smtplib.SMTPAuthenticationError as e:
            msg = f"SMTP Authentication failed for {self.email_address} while logging into smtp.gmail.com"
            self.logger.error(msg, exc_info=True)
            print(msg)
            exit(1)
        except Exception as e:
            msg = f"Unable to Log in to SMTP server (smtp.gmail.com) with credentials for {self.email_address}"
            self.logger.error(msg, exc_info=True)
            print(msg)
            exit(1)

    def get_changed_modules(self):
        """Get the list of changed modules from git"""

        self.logger.debug("Getting a list of changed modules from git")
        cmd = "git status --porcelain | awk {'print $2'} | grep module_ | cut -d '/' -f2 | sort | uniq"
        changed_modules = os.popen(cmd).read()
        changed_modules = changed_modules.strip()
        changed_modules = changed_modules.split("\n")

        return changed_modules

    def get_changed_files(self, module, results):
        """Get a list of changed files from git"""

        self.logger.debug(f"Getting a list of all changed files for {module} from git")
        cmd = f"git status --porcelain ./modules/{module}"
        changed_files = os.popen(cmd).read()
        changed_files = changed_files.strip()

        results += f"\n{module}"
        results += "\n" + "=" * 100 + "\n"
        results += "Changed files:\n"
        results += "-" * 14 + "\n"
        results += changed_files
        results += "\n" + "=" * 100 + "\n"

        return results

    def check_pylint(self):
        """Pull the pylint Docker image if it doesn't exist yet"""

        self.logger.debug("Checking whether the pylint Docker image is available")
        cmd = "docker images | grep cozero/linter-python3-pylint"
        pylint = os.popen(cmd).read()

        if not pylint:
            print("Pulling pylint Docker image")
            cmd = "docker pull cozero/linter-python3-pylint"
            os.system(cmd)

    def run_pylint(self, module, results):
        """Run code quality over the changed code"""

        self.logger.debug(f"Running pylint on {module} code")
        cmd = f"docker run --rm -v `pwd`:/app cozero/linter-python3-pylint modules/{module}"
        pylint_results = os.popen(cmd).read()
        results += pylint_results

        return results

    def copy_build_files(self, module, module_number):
        """Copy files and directories to the build directory and create a Dockerfile"""

        self.logger.debug(f"Copying build files to temporary staging area for {module}")

        # Standard base files that always need to be included in the build
        base_files = ("main.py", "requirements.txt", "setup.py")

        # Copy base files to the build directory
        for base_file in base_files:
            shutil.copy2("modules/" + base_file, "build/")

        # Work around for caching bug in distutils
        # Reference : https://stackoverflow.com/questions/9160227/dir-util-copy-tree-fails-after-shutil-rmtree
        dir_util._path_created = {}

        # Copy module directories to the build directory
        dir_util.copy_tree("modules/module_base", "build/module_base")
        dir_util.copy_tree(f"modules/{module}", f"build/{module}")

        # Copy the base Dockerfile across to the build directory
        shutil.copy2("docker/Dockerfile", "build/")

        # Add the container start-up command to the Dockerfile
        f = open("build/Dockerfile", "a+")
        f.write(f'CMD ["python3.6", "main.py", "{module_number}"]')
        f.close()

    def build_docker_image(self, module, tag):
        """Build and tag the Docker image"""

        self.logger.info(f"Building Docker image for {module}:{tag}")
        cmd = f"docker build build/ -t {module}:{tag} -f build/Dockerfile > /dev/null 2>&1"
        os.system(cmd)

    def tag_release(self):
        """Commit the new code and tag the release in git"""

        cmd = "git describe --tags $(git rev-list --tags --max-count=1)"
        latest_tag = os.popen(cmd).read()
        matches = re.findall("v(\d+)", latest_tag)

        version = matches[0]
        version = int(version)
        version = version + 1

        new_tag = "v" + str(version)
        self.logger.info(f"Committing code and tagging new release as {new_tag}")

        cmd = "git add --all"
        os.system(cmd)

        cmd = f'git commit -m "Release {new_tag}"'
        os.system(cmd)

        cmd = f"git tag {new_tag}"
        os.system(cmd)

        return new_tag


    def tag_gcr_image(self, gcr_image, module, tag):
        """Tag the docker image for GCP Container Registry"""

        self.logger.info(f"Tagging image {module}:{tag} as {gcr_image} for GCR Push")
        cmd = f"docker tag {module}:{tag} {gcr_image}"

        return os.system(cmd)


    def push_gcr_image(self, gcr_image):
        """Push the image to the Container Registry"""

        self.logger.info(f"Pushing {gcr_image} to GCR")
        cmd = f"docker push {gcr_image} > /dev/null 2>&1"

        return os.system(cmd)


    def create_yaml(self, module_number, gcr_image):
        """Create the YAML file to inject the environment variables to Kubernetes"""

        self.logger.info(f"Creating build/build.yaml file which describes the Deployment information for module-{module_number}")

        f = open("build/build.yaml", "w+")
        f.write("apiVersion: apps/v1\n")
        f.write("kind: Deployment\n")
        f.write("metadata:\n")
        f.write(f"  name: module-{module_number}\n")
        f.write("spec:\n")
        f.write("  replicas: 2\n")
        f.write("  selector:\n")
        f.write("    matchLabels:\n")
        f.write(f"      app: module-{module_number}\n")
        f.write("  template:\n")
        f.write("    metadata:\n")
        f.write("      labels:\n")
        f.write(f"        app: module-{module_number}\n")
        f.write("    spec:\n")
        f.write("      containers:\n")
        f.write(f"      - name: module-{module_number}\n")
        f.write(f"        image: {gcr_image}\n")
        f.write("        env:\n")
        f.write("        - name: MODULE_NUMBER\n")
        f.write(f'          value: "{module_number}"\n')
        f.close()


    def deploy_to_kubernetes(self, module_number, gcr_image):
        """Set environment variables and deploy container to Kubernetes"""

        self.logger.info(f"Deploying module-{module_number} to Kubernetes")
        cmd = ["kubectl", "get", "deployment", f"module-{module_number}"]

        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                )

        stdout, stderr = proc.communicate()
        deployment_status = str(stderr)
        matches = re.findall("No resources found", deployment_status)

        """Create a new deployment if the module isn't yet deployed, or
        alternatively, update the image to new image if a deployment exists"""
        if len(matches):
            self.create_yaml(module_number, gcr_image)
            cmd = "kubectl apply -f build/build.yaml > /dev/null 2>&1"
        else:
            cmd = f"kubectl set image deployment/module-{module_number} module-{module_number}={gcr_image}"

        return os.system(cmd)


    def send_notification(self, results):
        """Send notification email to administrator"""

        self.logger.info("Sending email notification to the administrator")

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = self.admin
            msg['Subject'] = "Insights Pty Ltd Deployment Status"
            msg.attach(MIMEText(results, 'plain'))

            text = msg.as_string()

            self.smtp_server.sendmail(self.email_address, self.admin, text)
            self.smtp_server.quit()
            self.logger.info(f"Notification email sent to {self.admin} successfully")
        except Exception as e:
            msg = f"An error occurred attempting to send the notification email to {self.admin}"
            self.logger.error(msg, exc_info=True)
            print(msg)
