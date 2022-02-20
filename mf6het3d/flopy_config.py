'''
Flopy configuration file
'''

# Python dependencies
import os
import sys
import flopy
import pickle
import argparse
import numpy as np
import pandas as pd
import shapely.geometry as shp
import matplotlib.pyplot as plt


# Arguments 
parser = argparse.ArgumentParser( description='Setup modflow 6 simulation.' )
parser.add_argument( '--experiment', type=str, help='experiment to be configured' )
parser.add_argument( '--write'     , action='store_true', help='write simulation' )
args   = parser.parse_args()


# Configuration function
def configure(
        simulation_name   = None,
        model_name        = None,
        pumping_flow_rate = None, 
        specific_storage  = None, 
        newton_raphson    = None, 
        head_convergence  = None, 
        hk_field_variance = None, 
    ):

    # Parse model parameters and define 
    # default values 
    if head_convergence is None:
        head_convergence = 1e-6
    if hk_field_variance is None:
        hk_field_variance = 2.25
    if pumping_flow_rate is None:
        pumping_flow_rate = 50 # l/min
    if specific_storage is None:
        specific_storage = 0.01 # 1/m
    if simulation_name is None:
        sim_directory       = 'mf6_sim'
        sim_name            = 'mf6_sim'
    else:
        sim_directory       = os.path.join( experiment_folder, simulation_name )
        sim_name            = simulation_name
    if model_name is None:
        model_name          = 'mf6_model'


    ############################
    # General model parameters #
    ############################
    inner_maximum_iterations = 250 
    outer_maximum_iterations = 100
    newton_raphson           = True
    current_dir              = os.getcwd()
    data_dir                 = os.path.join( current_dir, 'data' )
    
    
    ################
    # Load HK data #
    ################
    # This file was generated with sgems. 
    # Contains 100X100X10 cells 
    hk_field_file     = 'hk_field.csv'
    hk_df             = pd.read_csv( os.path.join( data_dir, hk_field_file ) )
    hk_array          = hk_df.to_numpy().reshape(100,100,10)
    hk_array          = np.swapaxes( hk_array, 0, 2 )
    # This array should have as shape
    # (number_of_layers, number_of_columns, number_of_rows )
    hk_array = np.exp( np.sqrt(hk_field_variance)*hk_array ) # Considered as m/day
    
    
    stress_periods = [
            {
                'id'           : 0,
                'length'       : 100,    # Days
                'n_time_steps' : 1, 
                'ts_multiplier': 1,
                'steady_state' : True
            },
            {
                'id'           : 1,
                'length'       : 1/24,    # Days
                'n_time_steps' : 15, 
                'ts_multiplier': 1,
                'steady_state' : False
            },
            {
                'id'           : 2,
                'length'       : 1/24,    # Days
                'n_time_steps' : 15, 
                'ts_multiplier': 1,
                'steady_state' : False
            },
            {
                'id'           : 3,
                'length'       : 1/24,    # Days
                'n_time_steps' : 15, 
                'ts_multiplier': 1,
                'steady_state' : False
            },
        ]
    
    
    
    ###################
    # Simulation data #
    ###################
    mf6_executable      = 'mf6'  # In windows remember to specify the full path to exe
    
    # Initializes flopy sim
    sim = flopy.mf6.MFSimulation(
            sim_name=sim_name,
            sim_ws  =sim_directory,
            exe_name=mf6_executable
        )
    
    
    ########################
    # Timing configuration #
    ########################
    # Configure stress periods data 
    # based on stress_periods variable definition
    perioddata = []
    for sp in stress_periods:
        perioddata.append( [sp['length'], sp['n_time_steps'], sp['ts_multiplier']] )
    
    # Initializes flopy time discretization
    tdis = flopy.mf6.ModflowTdis(
        sim,
        nper=len(stress_periods),
        perioddata=perioddata,
    )
    
    
    ##########################
    # Iterative Model Solver #
    ##########################
    # Important: MF6 requires this package.
    # Without its definition, raises an error
    ims = flopy.mf6.ModflowIms(
            sim,
            pname        ='ims',
            print_option ='SUMMARY',
            complexity   ='MODERATE', # It could be 'simple', 'moderate', 'complex'
    # LINEAR SOLVER BLOCK
            inner_maximum      = inner_maximum_iterations, # Number of iterations
            inner_hclose       = head_convergence,         # Convergence criteria, same dimensions as head
            linear_acceleration= 'BICGSTAB',
            scaling_method     = 'NONE',
            reordering_method  = 'NONE',
            relaxation_factor  = 0.97,
    # NON LINEAR SOLVER BLOCK (If using Newton-Raphson)
            outer_maximum      = outer_maximum_iterations,  # Number of iterations 
            outer_hclose       = head_convergence,          # Convergence criteria, same dimensions as head
            no_ptcrecord       = ['ALL'], 
    )
    
    
    ########################
    # Initialize GWF Model #
    ########################
    if newton_raphson:
        gwf = flopy.mf6.ModflowGwf(
            sim,                                     
            modelname=model_name,
            save_flows=True,
            newtonoptions=['UNDER_RELAXATION'], # Newton
        )
    else:
        gwf = flopy.mf6.ModflowGwf(
            sim,                                     
            modelname=model_name,
            save_flows=True,
        )
    
    
    
    ###################
    # Initialize Grid #
    ###################
    
    # Define domain_data
    # as a function of hk_field
    domain_data = {
            'length': hk_array.shape[1],
            'width' : hk_array.shape[2],
            'bottom': 0,
            'top'   : hk_array.shape[0],
            'discretization': {
                'columns': hk_array.shape[1],  # length
                'rows'   : hk_array.shape[2],  # width
                'layers' : hk_array.shape[0],  # depth 
            },
        }
    
    
    # Define the bottom of each layer, 
    # actually useful for the multilayer case
    # Same height layers
    bottom_array = np.linspace(
            domain_data['top'] - (domain_data['top'] - domain_data['bottom'])/(domain_data['discretization']['layers']),
            domain_data['bottom'],
            domain_data['discretization']['layers']
        )
    
    # Build discretization
    dis = flopy.mf6.ModflowGwfdis(
            gwf, 
            nlay=domain_data['discretization']['layers'],
            nrow=domain_data['discretization']['rows'],
            ncol=domain_data['discretization']['columns'],
            delr=domain_data['length']/domain_data['discretization']['columns'],
            delc=domain_data['width'] /domain_data['discretization']['rows'],
            top =domain_data['top'],
            botm=bottom_array
        )
    
    
    ######################
    # Node property flow #
    ######################
    
    # Initialize npf package
    icelltype = 0 # 0: saturated thickness constant, 1: varies with head
    npf = flopy.mf6.ModflowGwfnpf(
        gwf,
        save_specific_discharge=True, 
        icelltype=icelltype,
        k=hk_array,
    )
    
    
    #################
    # Constant Head #
    #################
    # Note that when icelltype = 1, then
    # the constant head property should be 
    # consistent with bottom of the layers.
    # Meaning, the condition has to be applied for those 
    # layers whose bottom is less than the constant head
    
    # For this case initializes a 
    # unit hydraulic gradient, that is
    # dh/dl = 0.1 In this case dl = 100
    constant_head_data = [
            {
                'name': 'inlet',
                'head': 110,
                'line': shp.LineString(
                    [
                        shp.Point(0, domain_data['width']),
                        shp.Point(0, 0),
                    ]
                ),
            },
            {
                'name': 'outlet',
                'head': 100,
                'line': shp.LineString(
                    [
                        shp.Point(domain_data['length'], domain_data['width']),
                        shp.Point(domain_data['length'], 0.)
                    ]
                ),
            },
        ]
    
    
    # Initializes intersection object
    ginter = flopy.utils.GridIntersect( gwf.modelgrid )
    
    
    # Intersect each boundary location
    # with domain and apply
    chd_stress_period = []
    for ch in constant_head_data:
    
        # intersect holds 'cellids' property
        # for structured grid these follow row,column notation
        # whereas for disv or disu grids follow layer,cellid notation
        intersect = ginter.intersect( ch['line'] )
        
        # Apply it to all layers
        # Structured grid
        for layer in range(domain_data['discretization']['layers']):
            for cell in intersect['cellids']:
                chd_stress_period.append( [ (layer, cell[0], cell[1]), ch['head'] ] )
    
    # Initializes chd package
    chd = flopy.mf6.ModflowGwfchd(
            gwf,
            stress_period_data=chd_stress_period,
            maxbound=len(chd_stress_period)
        )
    
    
    ######################
    # Initial Conditions #
    ######################
    # Where the model will start the 
    # iterations. If closer to the solution, 
    # faster execution
    ic_array= np.zeros(
            (
                domain_data['discretization']['layers'],
                domain_data['discretization']['columns'],
                domain_data['discretization']['rows'],
            ), dtype=np.float64)
    
    # Linear interpolation for initial conditions
    # for each row
    aux_row_dis = np.arange(1, domain_data['discretization']['columns'] + 1 , 1)
    for ir in range(domain_data['discretization']['rows']):
        ic_array[0, :, ir] = (1 - aux_row_dis/domain_data['discretization']['columns'])*constant_head_data[0]['head'] + \
                             aux_row_dis/domain_data['discretization']['columns']*constant_head_data[1]['head']
    
    # Initializes initial conditions package
    ic = flopy.mf6.ModflowGwfic(
            gwf,
            strt=ic_array,
        )
    
    #########
    # Wells #
    #########

    wells_data = [
        {
            'id': 'W1',
            'point': shp.Point(25, 50),
            'screen_bottom': 1, # Relative to the bottom. In this case is zero.
            'screen_top'   : 2,
            'cellids'      : '',
            'layers'       : [],
            'pumping'      : [
                {
                    'stress_period_id': 0,
                    'flow_rate': 0,
                },
                {
                    'stress_period_id': 1,
                    'flow_rate': -pumping_flow_rate*1440/1000, # negative sign for extraction (factor convers to m/day)
                },
                {
                    'stress_period_id': 2,
                    'flow_rate': 0,
                },
                {
                    'stress_period_id': 3,
                    'flow_rate': 0,
                }
            ],
        },
        {
            'id': 'W2',
            'point': shp.Point(75, 50),
            'screen_bottom': 1, # Relative to the bottom. In this case is zero.
            'screen_top'   : 2,
            'cellids'      : '',
            'layers'       : [],
            'pumping'      : [
                {
                    'stress_period_id': 0,
                    'flow_rate': 0,
                },
                {
                    'stress_period_id': 1,
                    'flow_rate': pumping_flow_rate*1440/1000, # negative sign for extraction (factor convers to m/day)
                },
                {
                    'stress_period_id': 2,
                    'flow_rate': 0,
                },
                {
                    'stress_period_id': 3,
                    'flow_rate': 0,
                }
            ]
        },
        {
            'id': 'W3',
            'point': shp.Point(50, 25),
            'screen_bottom': 3, # Relative to the bottom. In this case is zero.
            'screen_top'   : 4,
            'cellids'      : '',
            'layers'       : [],
            'pumping'      : [
                {
                    'stress_period_id': 0,
                    'flow_rate': 0,
                },
                {
                    'stress_period_id': 1,
                    'flow_rate': 0
                },
                {
                    'stress_period_id': 2,
                    'flow_rate': -pumping_flow_rate*1440/1000, # negative sign for extraction (factor convers to m/day)
                },
                {
                    'stress_period_id': 3,
                    'flow_rate': 0,
                },
            ]
        },
        {
            'id': 'W4',
            'point': shp.Point(50, 75),
            'screen_bottom': 3, # Relative to the bottom. In this case is zero.
            'screen_top'   : 4,
            'cellids'      : '',
            'layers'       : [],
            'pumping'      : [
                {
                    'stress_period_id': 0,
                    'flow_rate': 0,
                },
                {
                    'stress_period_id': 1,
                    'flow_rate': 0
                },
                {
                    'stress_period_id': 2,
                    'flow_rate': pumping_flow_rate*1440/1000, # negative sign for extraction (factor converts to m/day)
                },
                {
                    'stress_period_id': 3,
                    'flow_rate': 0,
                },
            ]
        },
    ] 
    
    
    
    # Intersect wells with the grid
    # and initializs cellids.
    # Wells are considered to be a single point/cell
    # from the surface perspective, without diameter
    BOTTOM_TOLERANCE = 1e-7
    
    for w in wells_data:
    
        intersect = ginter.intersect( w['point'] )
        w['cellids'] = intersect['cellids'] 
    
        # Indices tuple has only one element, 
        # with indices representing layers for the well
        layer_indices_tuple = np.where( 
                (bottom_array - w['screen_top'] < BOTTOM_TOLERANCE) & 
                (bottom_array - w['screen_bottom'] >= BOTTOM_TOLERANCE) 
            )
    
        # Assign layers 
        w['layers'] = list(layer_indices_tuple[0])
    
    
    
    # Initialize wel_stress_period dict
    # which is passed to the well package
    wel_stress_period = {}
    for sp in stress_periods:
        wel_stress_period[ sp['id'] ] = []
    
    # Populate wel_stress_period dict
    for w in wells_data:
    
        # If the well is not pumping, continue 
        # to the next
        if not w['pumping']:
            continue
    
        # Loop over pumping cycles/stress periods
        for wsp in w['pumping']:
    
            cellids = w['cellids'].item()
    
            w_stress_period = []
    
            # Apply flow rate to deepest layer,
            # increasing vertical k of upper layers
            # In the case of multiple layers
            npf_package  = gwf.get_package('npf')
            kxx_data     = npf_package.k.get_data()
            kxx_data[ w['layers'][:-1], cellids[0], cellids[1] ] = [ kxx*10 for kxx in kxx_data[ w['layers'][:-1], cellids[0], cellids[1] ] ]
            npf_package.k33.set_data(kxx_data)
            w_stress_period.append(
                    [
                        (w['layers'][-1], cellids[0], cellids[1]),
                        wsp['flow_rate'],
                        w['id'] + '_SP' + str(wsp['stress_period_id'])
                    ]
                )
            # Assign to stress period
            wel_stress_period[ wsp['stress_period_id'] ].extend( w_stress_period )
    
    # Build package
    wel = flopy.mf6.ModflowGwfwel(
            gwf,
            stress_period_data=wel_stress_period,
            boundnames=True,
            save_flows=True
        )
    
    ###########
    # Storage #
    ###########
    steady_state={}
    transient_state={}
    for sp in stress_periods:
        steady_state[sp['id']]    = sp['steady_state']
        transient_state[sp['id']] = not sp['steady_state']
    
    storage_data = {
            'specific_yield'   : 0.2,
            'specific_storage' : specific_storage,
            'convertible_cells': 1, # no=0, yes=1
        }
    
    # Initializes the package
    sto = flopy.mf6.ModflowGwfsto(
            gwf,
            save_flows=True,
            iconvert=storage_data['convertible_cells'],
            ss=storage_data['specific_storage'],
            sy=storage_data['specific_yield'],
            steady_state=steady_state,
            transient=transient_state
        )
    
    
    
    ##################
    # Output control #
    ##################
    budget_file = model_name + '.bud'
    head_file   = model_name + '.hds'
    oc = flopy.mf6.ModflowGwfoc(
            gwf,
            budget_filerecord=budget_file,
            head_filerecord  =head_file,
            saverecord=[('HEAD', 'ALL'), ('BUDGET', 'ALL')]
        )
    
    #############
    # Write MF6 #
    #############
    if args.write:
        sim.write_simulation()



if __name__=='__main__':


    #############################
    # Process experiment argument
    if args.experiment is None:
        raise Exception('flopy_config: requires --experiment parameter')
    base_dir          = os.getcwd() 
    experiment_folder = os.path.join( base_dir, args.experiment )
    if not os.path.exists(experiment_folder):
        raise Exception('flopy_config: experiment ' + args.experiment + ' not found in base_dir ' + base_dir )


    ################
    # Load scenarios
    scenarios = pd.read_csv( os.path.join( experiment_folder, 'csv', 'scenarios.csv'), index_col=0 )  
    
    print( 'flopy_config: configuring experiment ' + args.experiment )
    for idsc, sc in scenarios.iterrows():
        print( 'flopy_config: configuring scenario ' + str(idsc) )
        configure(**sc.to_dict())


    print('flopy_config: done!')
