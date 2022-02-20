# Heterogeneous 3D Multi Scenario
This example loads an heterogeneous hydraulic conductivity field saved in a ``data/hk_field.csv`` file.

Is a simple model with a regional gradient and four wells that work as dipoles and switch their pumping state one time.

This example manages multiple simulations, which is explained in the following.

## Modflow Executable
The path to the ``modflow`` executable should be defined at ``config.py``, the variable ``exe_name``

## Configuring simulations
At ``setup.py`` specify an experiment name and the model parameters. These are mixed in order to create multiple scenarios. 
Note that model parameters should be consistent with keyword arguments at ``configure`` function defined in ``flopy_config.py``.
Initialize scenarios configuration with:

```
python setup.py
```

Once scenarios are defined, write configuration files with the command: 

```
python flopy_config.py --experiment the_experiment_name --write
```

The latter will create one folder per each defined scenario at ``the_experiment_name/csv/scenarios.csv``.

## Run simulations
Simulations can be executed massivelly with the command: 
```
python run.py --experiment the_experiment_name --run
```

It is possible to specify also a range of indexes to be executed like this:

```
python run.py --experiment the_experiment_name --start 2 --end 4 --run
```

which will execute the range of simulations given by ``start`` and ``end`` values.


## flopy_config
This file contains the function configure which initializes the MF6 configuration. Is the one that interprets
parameters and create required ``flopy`` objects. 
