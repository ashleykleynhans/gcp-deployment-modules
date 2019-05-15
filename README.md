###  Bidvest Assessment

This assessment uses Python 3.6, GCP (Container Registry & Kubernetes), Docker, Git, and Ubuntu Linux 18.04 (LTS)

## Assumptions

1. All code is being committed, tagged and released on the master branch since there was no mention of the git flow process in the documentation.
2. Code quality checks are run and reported, but don't prevent a build from happening as the documentation didn't mention what the minimum requirements for code quality were for a build to pass.
3. You will already have installed and configured the Google Cloud SDK
4. A GMail account (which allows insecure app access) will be used to send emails (configured in setup.py)

Usually an actual production pipeline will have different branches, include automated testing and fail the build if the code quality doesn't meet certain conditions.

## Requirements

* Docker (https://www.docker.com/community-edition#/download)
* Google Cloud SDK (https://cloud.google.com/sdk/)

## Installation

1. Clone the repo

2. Change directory to the folder where you cloned the repo to

3. Complete the configuration in the modules/setup.py file

4. Build the initial application

    scripts/build.py

5. Make changes to a module, then deploy the changes

    scripts/deploy.py
