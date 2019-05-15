#!/usr/bin/env python3.6
import os
import shutil
import re
import glob

from deployment_base import DeploymentBase

"""This script builds and deploys the entire project"""


class Build(DeploymentBase):
    def __init__(self):
        super(Build, self).__init__()

    def build_modules(self):
        """Build All Docker Containers, push them to GCP, and deploy to Kubernetes"""

        print("Deployment Pipeline POC for Insights Pty Ltd")
        print("=" * 80)
        print(f"* Using config version: {self.version}")

        modules = glob.glob("modules/module_*")
        modules.sort()

        if not (len(modules)):
            raise Exception("No modules found")

        for module in modules:
            matches = re.findall("module_(\d+|base)", module)
            module_number = matches[0]
            module = "module_" + module_number

            # Don't build the base image
            if module_number == "base":
                continue

            # Remove the temporary build directory in case it somehow already exists
            shutil.rmtree("build", ignore_errors=True)

            cmd = "git describe --tags $(git rev-list --tags --max-count=1)"
            tag = os.popen(cmd).read()
            tag = tag.strip()

            if not tag:
                raise Exception("There are no git tags, create a git tag in order to build the project.")

            # Create the temporary build directory
            os.mkdir("build")

            gcr_image = f"{self.gcr_hostname}/{self.gcp_project}/{module}:{tag}"
            gcr_latest_image = f"{self.gcr_hostname}/{self.gcp_project}/{module}:latest"

            self.copy_build_files(module, module_number)
            self.build_docker_image(module, tag)
            exit_code = self.tag_gcr_image(gcr_image, module, tag)
            exit_code_latest = self.tag_gcr_image(gcr_latest_image, module, tag)

            if exit_code or exit_code_latest:
                print(f"* ({module}) Docker container image build FAILED!")
            else:
                print(f"* ({module}) Docker container image build SUCCESSFUL.")

                exit_code = self.push_gcr_image(gcr_image)
                exit_code_latest = self.push_gcr_image(gcr_latest_image)

                if exit_code or exit_code_latest:
                    print(f"* ({module}) Docker container image push to GCR FAILED!")
                else:
                    print(f"* ({module}) Docker container image push to GCR SUCCESSFUL.")

                    exit_code = self.deploy_to_kubernetes(module_number, gcr_image)

                    if exit_code:
                        print(f"* ({module}) Docker container deployment to Kubernetes FAILED!")
                    else:
                        print(f"* ({module}) Docker container deployment to Kubernetes SUCCESSFUL.")

            # Remove the temporary build directory now that the build is complete
            shutil.rmtree("build")


build = Build()
build.build_modules()
