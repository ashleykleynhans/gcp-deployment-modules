Python Version Python3.6

**Deploying a module** 

Package requirements will be installed via the ```requirements.txt```  file

The code can be run by running the below command 

```python 3.6 ./main.py```

A module will require the following items to run successfully 

- module_[1/2/3...] 
- module_base folder 
- requirements.txt 
- setup.py
- main.py

To deploy a module you will require to set the `MODULE_NUMBER` environment 
variable, if the environment variable is not set the code will raise an
exception that the `MODULE_NUMBER` is not set.

Each module will be mapped to a specific number, to run module 1 you will have
set the `MODULE_NUMBER` to the corresponding number for e.g `module_1`

Deployment status emails are sent to the email set in the `config.admin` 
in the `setup.py` file 
