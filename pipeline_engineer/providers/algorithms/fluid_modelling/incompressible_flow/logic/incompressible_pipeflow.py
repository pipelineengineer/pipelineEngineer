import os
from .incompressible_pres_thru_network import *
from ...general_logic.function_helpers import *
from ...pipeflow.logic.running_pipeflow import *
from ...fluids.logic.fluids import *
from .correct_directionality import *
from .dataframes_to_csv import *

def incompressible_flow(layers,args,
                             liquid_phase,
                             fluid_pres,fluid_temp,
                             load_network_skeleton,
                             chainage,dem_layer,vapour_pres,multiplier,
                             feedback):
    
    liquid_density = get_fluid_parameter(parameter='density',chosen_fluid=liquid_phase,temperature=fluid_temp,pressure=fluid_pres)
    liquid_viscosity = get_fluid_parameter(parameter='viscosity',chosen_fluid=liquid_phase,temperature=fluid_temp,pressure=fluid_pres)

    layers_for_pipeflow = []
    two_phase_layers = []
    
    for layer in layers:
        
        layer_name = layer.name().lower()
        
        if "(two-phase flow)" not in layer_name:
            layers_for_pipeflow.append(layer)
        else:
            two_phase_layers.append(layer)

    pipeflow_layers = run_pipeflow(layers=layers_for_pipeflow,fluid=liquid_phase,args=args,load_layers=False)
    
    pipeflow_result_layers = []
    
    for layer in pipeflow_layers:
        layer_name = layer.name().lower()
        
        if 'pipe layer' in layer_name:
            pipe_results_layer = layer
            
        elif 'junction layer' in layer_name:
            junction_layer = layer
        elif 'grid layer' in layer_name:
            grid_layer = layer
            pipeflow_result_layers.append(layer)
        elif 'pump layer' in layer_name:
            pump_layer = layer
            pipeflow_result_layers.append(layer)
            two_phase_layers.append(layer)
        else:
            pipeflow_result_layers.append(layer)
    
    feedback.pushInfo("Collecting line elevation profiles...")
    network_xyz, network_skeleton  = create_network_xyz_layer(pipe_results_layer=pipe_results_layer,
                                                             chainage=chainage,raster_layer=dem_layer,
                                                             load_layers=False)
    
    network_skeleton.setName('Network Skeleton')
    network_xyz.setName('Network XYZ Data')
    
    if load_network_skeleton:
        pipeflow_result_layers.append(network_xyz)
        pipeflow_result_layers.append(network_skeleton)
    
    line_data_df = layer_to_df(network_skeleton)
    line_xyz_df = layer_to_df(network_xyz)
    grids_df = layer_to_df(grid_layer)
    
    try:
        pump_df = layer_to_df(pump_layer)
    except:
        pump_df = pd.DataFrame()
    
    feedback.pushInfo("Calculating line pressures...")
    
    line_df, junction_df, master_results_df = incompressible_pres_through_network(network_df=line_data_df,network_xyz_df=line_xyz_df,
                                                                             boundaries_df=grids_df,
                                                                             liquid_density=liquid_density,liquid_viscosity=liquid_viscosity,
                                                                             vapour_pres=vapour_pres,fluid_temp=fluid_temp,multiplier=multiplier,two_phase_layers=two_phase_layers)

    dataframes = [line_df, junction_df,master_results_df]
    file_names = ['junction_results','pipe_results']
    
    file_names = ['junction_results','pipe_results','master_results']
    
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

            style_path = os.path.join(folder_path, 'pipe_res_pres.qml')

            re_calc_graduated(layer=joined_layer_pipe, qml_path=style_path)
        
            # adding to session
            joined_layer_pipe.setName('Two-Phase Pipe Results Layer')
            two_phase_layers.append(joined_layer_pipe)
        
        elif layer_name == 'junction_results':
            
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
            
        else:
            layer.selectAll()
            
            # Create output line layer (same CRS as input)
            crs = layer.crs()
            line_layer = QgsVectorLayer(f"LineString?crs={crs.authid()}", "Pressure Drop By Section", "memory")
            provider = line_layer.dataProvider()

            # Add fields (optional: copy attributes)
            provider.addAttributes(layer.fields())
            line_layer.updateFields()

            features = []

            for f in layer.getFeatures():
                start_x = f["xcoord"]
                start_y = f["ycoord"]
                end_x = f["end_xcoord"]
                end_y = f["end_ycoord"]

                # Create line geometry
                line = QgsGeometry.fromPolylineXY([
                    QgsPointXY(start_x, start_y),
                    QgsPointXY(end_x, end_y)
                ])

                new_feat = QgsFeature()
                new_feat.setGeometry(line)
                new_feat.setAttributes(f.attributes())

                features.append(new_feat)

            provider.addFeatures(features)
            line_layer.updateExtents()
            
            # applying layer style
            script_directory = os.path.dirname(os.path.abspath(__file__))
            folder_path = os.path.join(script_directory, 'layer_styles')
            os.makedirs(folder_path, exist_ok=True)

            style_path = os.path.join(folder_path, 'pres_drop_by_section.qml')

            re_calc_graduated(layer=line_layer, qml_path=style_path)
            
            two_phase_layers.append(line_layer)
            
    pipeflow_result_layers.extend(two_phase_layers)
    
    return pipeflow_result_layers