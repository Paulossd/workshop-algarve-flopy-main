'''
Execute simulations
'''

import os
import sys
import flopy
import pandas as pd
import numpy as np
import argparse


#################
# Administrative 
import config
base_dir = config.FOLDERS['base']


# Verify that exe_name is defined
try:
    config.exe_name
except Exception as e:
    print(e)
    raise Exception('run: exe_name not defined in config.')

# To config?
runscsv               = 'runs.csv'
discrepancy_threshold = 1 # Percentage

############
# Arguments 
parser = argparse.ArgumentParser( description='Execute simulations scenarios for a given experiment.' )
parser.add_argument( '--experiment', type=str, help='name of the experiment to be run' )
parser.add_argument( '--start'     , type=int, help='intial experiment index' )
parser.add_argument( '--end'       , type=int, help='final experiment index', )
parser.add_argument( '--run'       , action='store_true', help='run it' )
parser.add_argument( '--clean'     , action='store_true', help='forces restarting output runs.csv' )
args = parser.parse_args()


#############
# Experiment 
if args.experiment is None:
    raise Exception('run: --experiment was not defined')
experiment_name   = args.experiment
experiment_folder = os.path.join(base_dir, experiment_name)  
if not os.path.exists(experiment_folder):
    raise Exception('run: experiment ' + experiment_name + ' does not exists in output path.')

# Import scenarios
if not os.path.exists(os.path.join(experiment_folder, 'csv', 'scenarios.csv')):
    raise Exception('run: experiment ' + experiment_name + ' does without scenarios defined.')
scenariosdf = pd.read_csv(os.path.join(experiment_folder, 'csv', 'scenarios.csv'), index_col=0)


# Determine indexes
indexes = None
if args.start and args.end:
    indexes = np.arange(int(args.start), int(args.end), 1 ).astype(np.int32)
elif args.start:
    indexes = np.arange(int(args.start), len( SCENARIOS ), 1 ).astype(np.int32)
elif args.end:
    indexes = np.arange(0, int(args.end), 1 ).astype(np.int32)
else:
    indexes = None


# RUN
run_simulation = False
if args.run:
    run_simulation = True
else:
    print('run: not running. Force execution with --run')
    sys.exit()


# Import scenarios
if ( not os.path.exists(os.path.join(experiment_folder, 'csv', runscsv)) ) or ( args.clean ):
    # Initialize runsdf from sceanriosdf with status column pending
    runsdf           = scenariosdf.copy()
    runsdf['status'] = 'pending'
    runsdf.to_csv(os.path.join(experiment_folder, 'csv', runscsv) )
else:
    # Load runs
    runsdf = pd.read_csv(os.path.join(experiment_folder, 'csv', runscsv), index_col=0)

if indexes is None:
    if run_simulation:
        for index, sc in scenariosdf.iterrows():
       
            # Load simulation 
            simulation_folder = os.path.join(experiment_folder, sc['simulation_name']) 
            sim = flopy.mf6.MFSimulation.load(sim_ws=simulation_folder, sim_name=sc['simulation_name'], exe_name=config.exe_name)
            
            # Report status as running
            runsdf.loc[index,'status'] = 'running'
            runsdf.to_csv(os.path.join(experiment_folder, 'csv', runscsv) )

            # Execute 
            success, mf6_output = sim.run_simulation(pause=False, report=True)



            if not success:

                print('################ WARNING #################')
                warnings.warn('MF6 did not terminate normally for simulation ' + sc['simulation_name'])

                # Report status failed
                runsdf.loc[index,'status'] = 'failed'
                runsdf.to_csv(os.path.join(experiment_folder, 'csv', runscsv) )

                continue

            # Check convergence threshold for all stress periods
            # Load lst file
            mf_list_file  = flopy.utils.Mf6ListBudget( os.path.join(experiment_folder, sc['simulation_name'], sc['model_name']+'.lst') )
            dfflux, dfvol = mf_list_file.get_dataframes()
            
            # If all balances are less than N% discrepant, pass
            if (
                ( not np.all( dfvol['PERCENT_DISCREPANCY'].to_numpy() < discrepancy_threshold ) ) or
                ( not np.all( dfflux['PERCENT_DISCREPANCY'].to_numpy() < discrepancy_threshold ) )
            ):
                # Report status alert
                runsdf.loc[index,'status'] = 'alert'
                runsdf.to_csv(os.path.join(experiment_folder, 'csv', runscsv) )
            else:
                # Report status success
                runsdf.loc[index,'status'] = 'success'
                runsdf.to_csv(os.path.join(experiment_folder, 'csv', runscsv) )

else:
    if run_simulation:
        for index in indexes:
            sc = scenariosdf.iloc[index]
        
            # Load simulation
            simulation_folder = os.path.join(experiment_folder, sc['simulation_name']) 
            sim = flopy.mf6.MFSimulation.load(sim_ws=simulation_folder, sim_name=sc['simulation_name'], exe_name=config.exe_name)
            
            # Report status as running
            runsdf.loc[index,'status'] = 'running'
            runsdf.to_csv(os.path.join(experiment_folder, 'csv', runscsv) )

            # Execute
            success, mf6_output = sim.run_simulation(pause=False, report=True)

            if not success:
                print('################ WARNING #################')
                warnings.warn('MF6 did not terminate normally for simulation ' + sc['simulation_name'])

                # Report status failed
                runsdf.loc[index,'status'] = 'failed'
                runsdf.to_csv(os.path.join(experiment_folder, 'csv', runscsv) )

                continue

            # Check convergence threshold for all stress periods
            # Load lst file
            mf_list_file  = flopy.utils.Mf6ListBudget( os.path.join(experiment_folder, sc['simulation_name'], sc['model_name']+'.lst') )
            dfflux, dfvol = mf_list_file.get_dataframes()
            
            # If all balances are less than N% discrepant, pass
            if (
                ( not np.all( dfvol['PERCENT_DISCREPANCY'].to_numpy() < discrepancy_threshold ) ) or
                ( not np.all( dfflux['PERCENT_DISCREPANCY'].to_numpy() < discrepancy_threshold ) )
            ):
                # Report status alert
                runsdf.loc[index,'status'] = 'alert'
                runsdf.to_csv(os.path.join(experiment_folder, 'csv', runscsv) )
            else:
                # Report status success
                runsdf.loc[index,'status'] = 'success'
                runsdf.to_csv(os.path.join(experiment_folder, 'csv', runscsv) )



