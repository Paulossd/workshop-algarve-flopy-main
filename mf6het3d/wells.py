'''
wells.py
'''

import flopy
import numpy as np



def build(gwf, grid, wells, nper):
    '''
    Initializes flopy well package based on input params

    Input:
        - gwf   : flopy object
        - grid  : gridgen object
        - wells : dict with wells definition/config
        - nper  : number of stress periods
    '''
    ###########################
    # WHEN LAYERS ARE KNOWN
    ###########################
    
    WELLS=wells

    # Initialize wel_stress_period dict for wel pkg
    wel_stress_period = {}
    for sp in range(nper):
        wel_stress_period[ sp ] = []
    

    # Intersect wells with the grid
    for w in WELLS:

        w['grid_cells'] = grid.intersect([ (w['x'], w['y']) ], 'point', 0 )
        #w['grid_cells'] = grid.intersect([ (w['x'], w['y']) ], 'point', w['layers'][0] )

        # If the well is not pumping, continue 
        # to the next
        if not w['pumping']:
            continue
    
        # If the well has several layers
        # Apply pumping method if defined
        if len(w['layers']) > 1:
            try:
                sc['pumping_method']
                w['pumping_method'] = sc['pumping_method']
            except KeyError:
                w['pumping_method'] = 'distributed_by_transmissivities'
        else:
            # Fallback to single layer
            w['pumping_method'] = 'deepest_layer'
   
        # For DISV grid
        well_nodenumber = w['grid_cells'].nodenumber.item()
    
        # Loop over pumping cycles/stress periods
        for wsp in w['pumping']:
    
            w_stress_period = []
    
            if w['pumping_method'] == 'deepest_layer':
                # Apply flow rate to deepest layer without correcctions
                w_stress_period.append(
                        [
                            (w['layers'][-1], well_nodenumber),
                            wsp['flow_rate'],
                            w['id'] + '_SP' + str(wsp['stress_period_id'])
                        ]
                    )
    
            elif w['pumping_method'] == 'distributed_by_transmissivities':
                # Distribute flow rate based on transmissivities
                # Requires npf package
                bottom_array       = sc['gwf'].modelgrid.botm[:, well_nodenumber]
                model_layers_height= abs(np.diff(bottom_array)) # Substracts from the last item, removes the first
                well_layers_height = model_layers_height[ [ l-1 for l in w['layers'] ] ]
                npf_package        = sc['gwf'].get_package('npf')
                kxx_layers         = npf_package.k.array[w['layers'], well_nodenumber]
                
                if npf_package.k22.has_data():
                    kyy_layers   = npf_package.k22.array[w['layers'], well_nodenumber]
                    trans_layers = [ np.sqrt(kyy_layers[index]*kxx_layers[index])*l for index, l in enumerate(well_layers_height) ]
                else:
                    trans_layers = [ kxx_layers[index]*l for index, l in enumerate(well_layers_height) ]
    
                cell_flow_rates  = [ t*wsp['flow_rate']/sum(trans_layers) for t in trans_layers ]
    
                for index, layer in enumerate(w['layers']):
                    w_stress_period.append(
                        [
                            (layer, well_nodenumber),
                            cell_flow_rates[index],
                            w['id'] + '_SP' + str(wsp['stress_period_id'])
                        ]
                    )
    
            elif w['pumping_method'] == 'deepest_layer_kzz_correction':
                # Apply flow rate to deepest layer,
                # increasing vertical k of upper layers
                npf_package  = sc['gwf'].get_package('npf')
                kxx_data     = npf_package.k.get_data()
                kxx_data[ w['layers'][:-1], well_nodenumber ] = [ kxx*10 for kxx in kxx_data[ w['layers'][:-1], well_nodenumber ] ]
                npf_package.k33.set_data(kxx_data) # It works, verified in .wel files
                w_stress_period.append(
                        [
                            (w['layers'][-1], well_nodenumber),
                            wsp['flow_rate'],
                            w['id'] + '_SP' + str(wsp['stress_period_id'])
                        ]
                    )
    
            elif w['pumping_method'] == 'homogeneous':
                # Distribute flow rate homogeneously
                for layer in w['layers']:
                    w_stress_period.append(
                        [
                            (layer, well_nodenumber),
                            wsp['flow_rate']/len(w['layers']),
                            w['id'] + '_SP' + str(wsp['stress_period_id'])
                        ]
                    )
    
            else:
                raise Exception('setup.py: pumping method ' + w['pumping_method'] + ' not implemented.')
    
    
            # Assign to stress period
            wel_stress_period[ wsp['stress_period_id'] ].extend( w_stress_period )
   


    ###################
    # BUILD WEL PACKAGE
    ###################
    return flopy.mf6.ModflowGwfwel(
        gwf,
        stress_period_data=wel_stress_period,
        boundnames=True,
        save_flows=True
    )




if  __name__=='__main__':
    print('wells.py')
