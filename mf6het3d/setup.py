'''
Models setup manager
'''

# Python
import os
import sys
import numpy as np
import argparse

# Get directory of this file
# and append parent to sys.path
current = os.path.dirname(os.path.realpath(__file__))
parent  = os.path.dirname(current)
sys.path.append(parent)


# Self
from utils import scenarios
import config

# Arguments 
parser = argparse.ArgumentParser( description='Create model scenarios' )
parser.add_argument( '--experiment', type=str, help='name of the experiment' )
parser.add_argument( '--sim'       , type=str, help='base name for simulations' )
args = parser.parse_args()


# Simulations config
if args.experiment is None:
    experiment_name = 'test'
else:
    experiment_name = args.experiment
if args.sim is None:
    sim_base_name = 'SIM'
else:
    sim_base_name = args.sim

# Directories
base_dir          = config.FOLDERS['base']
experiment_folder = os.path.join( base_dir, experiment_name ) 

# Create experiment directories if not present
if not os.path.exists(experiment_folder):
    os.mkdir(os.path.join(experiment_folder))
if not os.path.exists(os.path.join(experiment_folder, 'csv')):
    os.mkdir(os.path.join(experiment_folder, 'csv'))


# Adjust parameters according to setup function
parameters = {
    'pumping_flow_rate'     : [50, 100], # l/min
    'specific_storage'      : [1e-2, 1e-3],
    'newton_raphson'        : [True, False],
    'head_convergence'      : [1e-5, 1e-6],
    'hk_field_variance'     : [1.25, 2.25],
}


# Create scenarios
scenariosdf = scenarios.combine(sim_base_name, **parameters)


# Save as csv
scenariosdf.to_csv(os.path.join(experiment_folder, 'csv', 'scenarios.csv'))


print('mf6het3d:setup: saved scenarios for experiment ' + experiment_name )
