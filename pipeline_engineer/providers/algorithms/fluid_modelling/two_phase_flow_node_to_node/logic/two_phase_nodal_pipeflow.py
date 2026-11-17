import os
from qgis.core import QgsProcessingException
from .two_phase_pres_thru_network_nodal import *
from ...general_logic.function_helpers import *
from ...pipeflow.logic.running_pipeflow import *
from ...fluids.logic.fluids import *
from .tp_node_correct_directionality import *
from .dataframes_to_csv import *

def two_phase_pipeflow_nodal(layers,args,
                             liquid_phase,gas_phase,
                             fluid_pres,fluid_temp,
                             k_h,salt_ppm,c_salt,salt_mol_mass,surf_tens,
                             apply_henrys_law,correct_salinity,correlation,
                             feedback):
    
    liquid_density = get_fluid_parameter(parameter='density',chosen_fluid=liquid_phase,temperature=fluid_temp,pressure=fluid_pres)
    liquid_viscosity = get_fluid_parameter(parameter='viscosity',chosen_fluid=liquid_phase,temperature=fluid_temp,pressure=fluid_pres)
    
    gas_molar_mass = get_fluid_parameter(parameter='molar_mass',chosen_fluid=gas_phase,temperature=fluid_temp,pressure=fluid_pres)
    gas_viscosity = get_fluid_parameter(parameter='viscosity',chosen_fluid=gas_phase,temperature=fluid_temp,pressure=fluid_pres)

    layers_for_pipeflow = []
    two_phase_layers = []
    
    for layer in layers:
        
        layer_name = layer.name().lower()
        crs = layer.crs()
        
        if "(two-phase)" not in layer_name:
            layers_for_pipeflow.append(layer)
        else:
            two_phase_layers.append(layer)

    if not two_phase_layers:
        
        raise QgsProcessingException("No two-phase sinks or sources are present in network.")
        return
    
    liquid_pipeflow = []
    gas_pipeflow = []

    liquid_pipeflow.extend(layers_for_pipeflow)
    gas_pipeflow.extend(layers_for_pipeflow)

    for layer in two_phase_layers:
        
        layer_name = layer.name().replace(' (Two-Phase) ',' ')

        liquid_source = processing.run("native:renametablefield", 
                                                    {'INPUT':layer,
                                                     'FIELD':'l_mdot_kg_per_s',
                                                     'NEW_NAME':'mdot_kg_per_s',
                                                     'OUTPUT':'memory:'})['OUTPUT']
        
        liquid_source.setName(f'Liquid {layer_name}')
        liquid_pipeflow.append(liquid_source)

        gas_source = processing.run("native:renametablefield", 
                                                    {'INPUT':layer,
                                                     'FIELD':'g_mdot_kg_per_s',
                                                     'NEW_NAME':'mdot_kg_per_s',
                                                     'OUTPUT':'memory:'})['OUTPUT']
        
        gas_source.setName(f'Gas {layer_name}')
        gas_pipeflow.append(gas_source)

    liquid_pipeflow_layers = run_pipeflow(layers=liquid_pipeflow,fluid=liquid_phase,args=args,load_layers=False)
    gas_pipeflow_layers = run_pipeflow(layers=gas_pipeflow,fluid=gas_phase,args=args,load_layers=False)

    pipeflow_result_layers = []
    
    for layer in liquid_pipeflow_layers:
        layer_name = layer.name().lower()
        
        if 'pipe layer' in layer_name:
            pipe_results_layer = layer
            
            field_names = pipe_results_layer.fields().names()
            
            if 'diameter_m' not in field_names:
                
                pipe_results_layer = processing.run("native:fieldcalculator", 
                                                            {'INPUT':pipe_results_layer,
                                                             'FIELD_NAME':'diameter_m',
                                                             'FIELD_TYPE':0,
                                                             'FIELD_LENGTH':0,
                                                             'FIELD_PRECISION':0,
                                                             'FORMULA':'"inner_diameter_mm"/1000',
                                                             'OUTPUT':'memory:'})['OUTPUT']
            
        elif 'junction layer' in layer_name:
            junction_layer = layer
        elif 'grid layer' in layer_name:
            grid_layer = layer
            pipeflow_result_layers.append(layer)
        elif 'pump layer' in layer_name:
            pump_layer = layer
            pipeflow_result_layers.append(layer)
        elif 'junction layer' in layer_name:
            junction_layer = layer
        else:
            pipeflow_result_layers.append(layer)

    for layer in gas_pipeflow_layers:
        layer_name = layer.name().lower()
        
        if 'pipe layer' in layer_name:
            
            gas_flows =  processing.run("native:fieldcalculator", 
                                                    {'INPUT':layer,
                                                     'FIELD_NAME':'g_mdot_kg_per_s',
                                                     'FIELD_TYPE':0,
                                                     'FIELD_LENGTH':0,
                                                     'FIELD_PRECISION':0,
                                                     'FORMULA':'ABS("mdot_from_kg_per_s")',
                                                     'OUTPUT':'memory:'})['OUTPUT']

            gas_flows.setName(layer_name)
        
        if 'source layer' in layer_name:
            
            pipeflow_result_layers.append(layer)

    feedback.pushInfo("Collecting line elevation profiles...")
    network_skel  = tp_create_network_skeleton(pipe_results_layer=pipe_results_layer,
                                                             load_layers=False)

    network_skeleton = processing.run("native:joinattributestable", 
                                                    {'INPUT':network_skel,
                                                     'FIELD':'name',
                                                     'INPUT_2':gas_flows,
                                                     'FIELD_2':'name',
                                                     'FIELDS_TO_COPY':['g_mdot_kg_per_s'],
                                                     'METHOD':1,
                                                     'DISCARD_NONMATCHING':False,
                                                     'PREFIX':'',
                                                     'OUTPUT':'memory:'})['OUTPUT']

    network_skeleton.setName('Network Skeleton')
    
    line_data_df = layer_to_df(network_skeleton)
    grids_df = layer_to_df(grid_layer)
    junction_heights_df = layer_to_df(junction_layer)
    
    try:
        pump_df = layer_to_df(pump_layer)
        pump_df = pd.DataFrame() 
    except:
        print('No pumps in system.')
        
    feedback.pushInfo("Calculating line pressures...")
    
    line_df, junction_df = two_phase_pres_through_network_nodal(network_df=line_data_df,boundaries_df=grids_df,junction_heights_df=junction_heights_df,
                                                                             liquid_density=liquid_density,liquid_viscosity=liquid_viscosity,
                                                                             gas_molar_mass=gas_molar_mass,gas_viscosity=gas_viscosity,fluid_temp=fluid_temp,
                                                                             k_h=k_h,salt_ppm=salt_ppm,c_salt=c_salt,salt_mol_mass=salt_mol_mass,
                                                                             surf_tens=surf_tens,apply_henrys_law=apply_henrys_law,correct_salinity=correct_salinity,correlation=correlation)

    dataframes = [line_df, junction_df]
    file_names = ['junction_results','pipe_results']
    
    file_names = ['junction_results','pipe_results']
    
    csv_files = dataframes_to_csv(dataframes,file_names)
    
    two_phase_layers = []
    
    feedback.pushInfo("Saving results to layers...")
    for layer in csv_files:
        layer_name = layer.name()
        
        print(layer_name)
        
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

            style_path = os.path.join(folder_path, 'pipe_res_pres_two_phase.qml')

            re_calc_graduated(layer=joined_layer_pipe, qml_path=style_path)
        
            # adding to session
            joined_layer_pipe.setName('Two-Phase Pipe Results Layer')
            two_phase_layers.append(joined_layer_pipe)
        
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
            
            two_phase_layers.append(null_removed)
            
    pipeflow_result_layers.extend(two_phase_layers)
    
    return pipeflow_result_layers