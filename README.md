# FloPy examples
This repository contains some example configuration files for using FloPy.

Each folder in this project is a different model case, with exception of ``utils`` which contains general usage functions.

## Download
Clone this repository with ``git`` or just download the compressed zip file through the repository page (green button "Code"). For ``git`` installation on ``windows`` follow the link at the bottom of this README.

## Python
Requires a working ``python3.*`` installation. If it is not installed, you can follow the instructions at the bottom.

## Virtual environment
It is recommended (but not strictly necessary) to create a virtual environment to keep isolated dependencies and packages.

Create a virtual enviroment named ``env`` with the command

```
python -m venv env
```

Activate the virtual environment. On ``Windows`` execute the command 

```
.\env\Scripts\activate
```

On ``linux``:

```
source env/bin/activate
```

For previous commands to work, be sure that current working directory corresponds to the same level where ``env`` has been created.

## Dependencies 
Once the virtual environment is activated, install project dependencies with the command:

```
pip install -r requirements.txt
```

If you prefer not to use a virtual environment, previous command should work likewise. Verify that is is being executed from this repository directory.

## MODFLOW
Download the MODFLOW executable and place it in a known folder. Save this address because is required by ``flopy`` to run models. On ``windows`` address to the MODFLOW executable should be written following the format:

```
C:\\thepathtoextractedmodflowfolder\\mf6.2.2\\bin\\mf6.exe
```

[Download MODFLOW](https://water.usgs.gov/water-resources/software/MODFLOW-6/mf6.2.2.zip)


## Verify 
Test that everything is working as expected by entering the ``mf6test`` folder of this repository. Open and edit the ``flopy_config.py`` file and replace the variable ``exe_name`` with the corresponding path to the MODFLOW executable. Then run:

```
python flopy_config.py
```
If there are no errors, the installation was successful.

## Resources 
[FloPy](https://github.com/modflowpy/flopy)

[Install ``python`` on windows](https://phoenixnap.com/kb/how-to-install-python-3-windows)

[``git`` for windows](https://git-scm.com/download/win)


