import os
from .pressure_through_a_network import *
from ...general_logic.function_helpers import *

def run_beggs_brill_pipeflow(network_skeleton, network_xyz,
                             grid_layer, junction_layer,
                             gas_density,gas_viscosity,
                             liquid_density, liquid_viscosity,
                             surf_tens, gas_fraction,load_layer):
    
    line_data_df = layer_to_df(network_skeleton)
    line_xyz_df = layer_to_df(network_xyz)
    grids_df = layer_to_df(grid_layer)
    
    line_df, junction_df = pressures_through_a_network(line_data_df, line_xyz_df,grids_df,
                            liquid_density, liquid_viscosity,
                            gas_density, gas_viscosity,
                            surf_tens,gas_fraction)

    dataframes = [line_df, junction_df]
    file_names = ['junction_results','pipe_results']
    
    result_layers = dataframes_to_csv(dataframes,file_names)
    
    layers_to_add = []
    
    for layer in result_layers:
        layer_name = layer.name()
        
        if layer_name == 'pipe_results':

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
            layers_to_add.append(joined_layer_pipe)
            
            if load_layer:
                QgsProject.instance().addMapLayer(joined_layer_pipe)
        
        else:
            
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
                                                 'PREFIX':'','OUTPUT':'memory:'})['OUTPUT']
            
            # applying layer style
            script_directory = os.path.dirname(os.path.abspath(__file__))
            folder_path = os.path.join(script_directory, 'layer_styles')
            os.makedirs(folder_path, exist_ok=True)

            style_path = os.path.join(folder_path, 'junction_res_pres.qml')

            re_calc_graduated(layer=joined_layer, qml_path=style_path)
        
            # adding to session
            joined_layer.setName('Two-Phase Junction Results Layer')
            
            layers_to_add.append(joined_layer)
            
            if load_layer:
                QgsProject.instance().addMapLayer(joined_layer)
            
    return layers_to_add
    