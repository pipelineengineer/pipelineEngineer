import os
from .pressure_through_a_network_hm import *
from ...general_logic.function_helpers import *
from ...pipeflow.logic.running_pipeflow import *
from ...fluids.logic.fluids import *
from .correct_directionality import *

def homogenous_model_pf(layers,pipeflow_fluid,args,
                             liquid_phase,gas_phase,
                             gas_frac,surf_tens,
                             gas_compressibility,molar_mass,
                             fluid_pres,fluid_temp,
                             load_network_skeleton,
                             chainage,dem_layer,feedback):
    
    liquid_density = get_fluid_parameter(parameter='density',chosen_fluid=liquid_phase,temperature=fluid_temp,pressure=fluid_pres)
    liquid_viscosity = get_fluid_parameter(parameter='viscosity',chosen_fluid=liquid_phase,temperature=fluid_temp,pressure=fluid_pres)
    
    pipeflow_layers = run_pipeflow(layers=layers,fluid=pipeflow_fluid,args=args,load_layers=False)
    
    beggs_brill_results = []
    
    for layer in pipeflow_layers:
        layer_name = layer.name().lower()
        
        if 'pipe layer' in layer_name:
            pipe_results_layer = layer
            
        elif 'junction layer' in layer_name:
            junction_layer = layer
        elif 'grid layer' in layer_name:
            grid_layer = layer
            beggs_brill_results.append(layer)
        elif 'pump layer' in layer_name:
            pump_layer = layer
            beggs_brill_results.append(layer)
        else:
            beggs_brill_results.append(layer)
    
    feedback.pushInfo("Collecting line elevation profiles...")
    network_xyz, network_skeleton  = create_network_xyz_layer(pipe_results_layer=pipe_results_layer,
                                                             chainage=chainage,raster_layer=dem_layer,
                                                             load_layers=False)
    
    network_skeleton.setName('Network Skeleton')
    network_xyz.setName('Network XYZ Data')
    
    if load_network_skeleton:
        beggs_brill_results.append(network_xyz)
        beggs_brill_results.append(network_skeleton)
    
    line_data_df = layer_to_df(network_skeleton)
    line_xyz_df = layer_to_df(network_xyz)
    grids_df = layer_to_df(grid_layer)
    
    try:
        pump_df = layer_to_df(pump_layer)
    except:
        pump_df = pd.DataFrame()
    
    
    print(line_data_df.head())
    print(line_xyz_df.head())
    print(grids_df.head())
    
    feedback.pushInfo("Calculating line pressures...")
    line_df, junction_df,master_results_df = pressures_through_a_network(line_data_df, line_xyz_df,grids_df,pump_df,
                            liquid_density, liquid_viscosity,gas_frac,gas_compressibility,molar_mass,surf_tens)

    dataframes = [line_df, junction_df,master_results_df]
    file_names = ['junction_results','pipe_results']
    
    file_names = ['bb_junction_results','bb_pipe_results','bb_master_results']
    
    csv_files = dataframes_to_csv(dataframes,file_names)
    
    beggs_brill_layers = []
    
    feedback.pushInfo("Saving results to layers...")
    for layer in csv_files:
        layer_name = layer.name()
        
        print(layer_name)
        
        if layer_name == 'bb_pipe_results':

            retained = processing.run("native:retainfields", 
                                                {'INPUT':network_skeleton,
                                                 'FIELDS':['name'],
                                                 'OUTPUT':'memory:'})['OUTPUT']

            joined_layer_pipe = processing.run("native:joinattributestable", 
                                                {'INPUT':retained,
                                                 'FIELD':'name',
                                                 'INPUT_2':layer,
                                                 'FIELD_2':'name',
                                                 'FIELDS_TO_COPY':[],
                                                 'METHOD':1,
                                                 'DISCARD_NONMATCHING':False,
                                                 'PREFIX':'','OUTPUT':'memory:'})['OUTPUT']
        
            # applying layer style
            script_directory = os.path.dirname(os.path.abspath(__file__))
            folder_path = os.path.join(script_directory, 'layer_styles')
            os.makedirs(folder_path, exist_ok=True)

            style_path = os.path.join(folder_path, 'pipe_res_pres.qml')

            re_calc_graduated(layer=joined_layer_pipe, qml_path=style_path)
        
            # adding to session
            joined_layer_pipe.setName('Two-Phase Pipe Results Layer')
            beggs_brill_layers.append(joined_layer_pipe)
        
        elif layer_name == 'bb_junction_results':
            
            retained = processing.run("native:retainfields", 
                                                {'INPUT':junction_layer,
                                                 'FIELDS':['name'],
                                                 'OUTPUT':'memory:'})['OUTPUT']

            joined_layer = processing.run("native:joinattributestable", 
                                                {'INPUT':retained,
                                                 'FIELD':'name',
                                                 'INPUT_2':layer,
                                                 'FIELD_2':'junction',
                                                 'FIELDS_TO_COPY':[],
                                                 'METHOD':1,
                                                 'DISCARD_NONMATCHING':False,
                                                 'PREFIX':'',
                                                 'OUTPUT':'memory:'})['OUTPUT']
            
            null_removed = processing.run("native:extractbyexpression", 
                                                {'INPUT':joined_layer,
                                                 'EXPRESSION':'"junction" IS NOT NULL',
                                                 'OUTPUT':'memory:'})['OUTPUT']
            
            # applying layer style
            script_directory = os.path.dirname(os.path.abspath(__file__))
            folder_path = os.path.join(script_directory, 'layer_styles')
            os.makedirs(folder_path, exist_ok=True)

            style_path = os.path.join(folder_path, 'junction_res_pres.qml')

            re_calc_graduated(layer=null_removed, qml_path=style_path)
        
            # adding to session
            null_removed.setName('Two-Phase Junction Results Layer')
            
            beggs_brill_layers.append(null_removed)
            
        else:
            layer.selectAll()
            
            working_layer = processing.run("native:saveselectedfeatures", 
                                                    {'INPUT':layer,
                                                     'OUTPUT':'memory:'})['OUTPUT']
            
            working_layer.setName('Two-Phase Pressure Drop By Section')
            
            beggs_brill_layers.append(working_layer)
            
    beggs_brill_results.extend(beggs_brill_layers)
    
    return beggs_brill_results