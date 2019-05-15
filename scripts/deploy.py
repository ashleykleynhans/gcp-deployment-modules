#!/usr/bin/env python3.6
import os
import shutil
import re

from deployment_base import DeploymentBase


"""This script deploys code changes"""


class Deployment(DeploymentBase):
    def __init__(self):
        super(Deployment, self).__init__()

    def deploy_modules(self):
        """Build Docker Containers, push them to GCP, and deploy to Kubernetes"""

        # This is where we will store the results that get emailed
        results = ""

        print("Deployment Pipeline POC for Insights Pty Ltd")
        print("=" * 80)
        print(f"* Using config version: {self.version}")

        self.check_pylint()
        changed_modules = self.get_changed_modules()

        for module in changed_modules:
            matches = re.findall("module_(\d+|base)", module)

            if not matches:
                print("No modules have changed, no deployment necessary at this time.")
                exit(1)

            module_number = matches[0]

            # Don't build the base image
            if module_number == "base":
                continue

            # Remove the temporary build directory in case it somehow already exists
            shutil.rmtree("build", ignore_errors=True)

            results = self.get_changed_files(module, results)
            results = self.run_pylint(module, results)
            tag = self.tag_release()

            # Create the temporary build directory
            os.mkdir("build")

            gcr_image = f"{self.gcr_hostname}/{self.gcp_project}/{module}:{tag}"
            gcr_latest_image = f"{self.gcr_hostname}/{self.gcp_project}/{module}:latest"

            self.copy_build_files(module, module_number)
            self.build_docker_image(module, tag)
            exit_code = self.tag_gcr_image(gcr_image, module, tag)
            exit_code_latest = self.tag_gcr_image(gcr_latest_image, module, tag)

            if exit_code or exit_code_latest:
                results += f"\n* ({module}) Docker container image build FAILED!\n"
            else:
                results += f"\n* ({module}) Docker container image build SUCCESSFUL.\n"

                exit_code = self.push_gcr_image(gcr_image)
                exit_code_latest = self.push_gcr_image(gcr_latest_image)

                if exit_code or exit_code_latest:
                    results += f"* ({module}) Docker container image push to GCR FAILED!\n"
                else:
                    results += f"* ({module}) Docker container image push to GCR SUCCESSFUL.\n"

                    exit_code = self.deploy_to_kubernetes(module_number, gcr_image)

                    if exit_code:
                        results += f"* ({module}) Docker container deployment to Kubernetes FAILED!\n"
                    else:
                        results += f"* ({module}) Docker container deployment to Kubernetes SUCCESSFUL.\n"

            # Remove the temporary build directory now that the build is complete
            shutil.rmtree("build")

        self.send_notification(results)


deployment = Deployment()
deployment.deploy_modules()
