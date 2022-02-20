# python
import os
import numpy as np
import pandas as pd
from itertools import product


def combine(sim_base_name, **kwargs):
    '''

    Given a list of keyword arguments, which entries 
    are parameter names to be modeled, the function 
    creates a list of scenarios mixing those parameters
    
    @params:
        sim_base_name (str): base simulation name
        **kwargs     (dict): dictionary of parameters (keys) and values

    @return:
        pandas.DataFrame() with columns simulation_name, model_name and parameters
    '''

    if not kwargs:
        raise Exception('scenarios.combine: no keyword arguments given.')

    # Count the number of scenarios
    number_of_scenarios = 1
    variables_values = []
    for variable, values in kwargs.items():
    
        # If not list, transform and append
        if not isinstance(values, (list, np.ndarray)):
            variables_values.append([values])
            continue
        
        # If list append
        number_of_scenarios = number_of_scenarios*len(values)
        variables_values.append(values)
    
    
    df = pd.DataFrame.from_records(
            list( i for i in product( *variables_values ) ),
            columns=kwargs.keys()
        )
    
    # Create simulation and model names columns and consolidate dataframe
    id_array                    = df.index.to_numpy()
    outputdf                    = pd.DataFrame()
    outputdf['simulation_name'] = np.core.defchararray.add( np.repeat(sim_base_name, len(id_array)) , id_array.astype(str) )
    outputdf['model_name']      = np.core.defchararray.add( outputdf['simulation_name'].to_numpy().astype(str), np.repeat('_MODEL', len(id_array)) )
    outputdf                    = pd.concat([outputdf, df], axis=1)


    return outputdf


