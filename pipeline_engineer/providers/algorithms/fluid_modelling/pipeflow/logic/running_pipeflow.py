import os
import processing

from qgis.core import (QgsVectorLayer,QgsField,QgsFields,QgsFeature,QgsGeometry,QgsPointXY,QgsProject, QgsMapLayer)

import pandapipes
import pandas as pd

mapping = {
    "junction layer": ["junction", "res_junction", pandapipes.create_junction,'junction_results.qml'],
    "pipe layer": ["pipe", "res_pipe", pandapipes.create_pipe_from_parameters,'pipe_results.qml'],
    "valve layer": ["valve", "res_valve", pandapipes.create_valve,None],
    "sink layer": ["sink", "res_sink", pandapipes.create_sink,None],
    "source layer": ["source", "res_source", pandapipes.create_source,None],
    "mass storage layer": ["mass_storage", "res_mass_storage", pandapipes.create_mass_storage,None],
    "grid layer": ["ext_grid", "res_ext_grid", pandapipes.create_ext_grid,None],
    "heat exchanger layer": ["heat_exchanger", "res_heat_exchanger", pandapipes.create_heat_exchanger,None],
    "pump layer": ["pump", "res_pump", pandapipes.create_pump,None],
    "circulation pump mass layer": ["circ_pump_mass", "res_circ_pump_mass", pandapipes.create_circ_pump_const_mass_flow,None],
    "circulation pump pressure layer": ["circ_pump_pressure", "res_circ_pump_pressure", pandapipes.create_circ_pump_const_pressure,None],
    "compressor layer": ["compressor", "res_compressor", pandapipes.create_compressor,None],
    "pressure control layer": ["press_control", "res_press_control", pandapipes.create_pressure_control,None],
    "flow control layer": ["flow_control", "res_flow_control", pandapipes.create_flow_control,None]
}

def layer_to_df(layer):
        cols = [f.name() for f in layer.fields()]
        data = ([f[col] for col in cols] for f in layer.getFeatures())
        df = pd.DataFrame.from_records(data=data, columns = cols)
        return df

def re_calc_graduated(layer, qml_path):
    layer.loadNamedStyle(qml_path)
    renderer = layer.renderer()

    if renderer.type() == 'graduatedSymbol':
        field_name = renderer.classAttribute()
        attr_index = layer.fields().indexOf(field_name)

        # Most builds (like yours) want both layer and field index
        try:
            renderer.updateClasses(layer, attr_index)
        except TypeError:
            # fallback for older versions that expect field name instead
            renderer.updateClasses(layer, field_name)

        # Reapply and refresh
        layer.setRenderer(renderer)
        layer.triggerRepaint()

def return_network_component_type(component_layer):
    component = component_layer.name()
    comp_lower = component.lower()

    component_list = list(mapping.keys())

    for item in component_list:
          
          if item in comp_lower:
                comp_key = item
                break
    
    component_type = mapping[comp_key][0]

    return component_type

def create_component(component, arg):
    if not isinstance(component, str):
        component = component.name()

    comp_lower = component.lower()

    # Mapping keywords to pandapipes creation functions

    # Find and call the correct function
    for key, value in mapping.items():
        if key in comp_lower:
            func = value[2]
            return func(**arg)  # Call the function with arguments

def on_create_network_clicked(components, selected_fluid):

    # components contains QgsVectorLayer objects (from Processing)
    # Make sure of that:
    layers = []
    for c in components:
        if isinstance(c, QgsVectorLayer):
            layers.append(c)
        else:
            # convert name → layer (if Processing ever returns strings, just in case)
            lyr = QgsProject.instance().mapLayersByName(c)
            if lyr:
                layers.append(lyr[0])

    # ---------------------------------------------------------
    # ORDER LAYERS: junctions → pipes → everything else
    # ---------------------------------------------------------
    ordered_components = []

    # junctions first
    for lyr in layers:
        if "junction" in lyr.name().lower():
            ordered_components.append(lyr)

    # pipes second
    for lyr in layers:
        if "pipe" in lyr.name().lower():
            ordered_components.append(lyr)

    # remaining components
    for lyr in layers:
        lname = lyr.name().lower()
        if "junction" not in lname and "pipe" not in lname:
            ordered_components.append(lyr)

    # Now the components list is clean
    components = ordered_components

    # ---------------------------------------------------------
    # CREATE NETWORK
    # ---------------------------------------------------------
    net = pandapipes.create_empty_network(fluid=selected_fluid)

    # Track junction table (needed for mapping)
    junction_df = None

    # ---------------------------------------------------------
    # ADD COMPONENTS
    # ---------------------------------------------------------
    for layer in components:

        print("Processing layer:", layer.name())

        component_df = layer_to_df(layer)
        component_df_columns = component_df.columns.tolist()

        # Detect junction-related fields
        junction_fields = [
            "junction", "controlled_junction", "flow_junction",
            "from_junction", "return_junction", "to_junction"
        ]

        common_values = set(component_df_columns) & set(junction_fields)

        # JUNCTION LAYER → create index
        if "junction" in layer.name().lower():
            component_df['index'] = component_df.index
            junction_df = component_df.copy()

        # OTHER COMPONENTS → map junction references to indexes
        elif junction_df is not None and common_values:
            for field in common_values:
                component_df[field] = component_df[field].map(
                    junction_df.set_index('name')['index']
                )

        # drop useless columns
        if 'fid' in component_df_columns:
            component_df_columns.remove('fid')

        # -----------------------------------------------------
        # CREATE COMPONENTS IN NETWORK
        # -----------------------------------------------------
        for i in range(len(component_df)):
            arg = {'net': net}
            for column in component_df_columns:
                arg[column] = component_df[column][i]

            create_component(component=layer, arg=arg)

    return net


def return_component_result(net,component):
        if type(component) != str:
            component = component.name()

        comp_lower = component.lower()

        for key, value in mapping.items():
                if key in comp_lower:
                # Use getattr safely, raise error if missing
                        attr_name = value[1]
                        if hasattr(net, attr_name):
                                return getattr(net, attr_name)
                        else:
                                raise AttributeError(f"The network has no component '{attr_name}'")

        raise ValueError(f"No matching component found for '{component}'")

def return_network_component(net, component):
    if not isinstance(component, str):
        component = component.name()

    comp_lower = component.lower()

    # Map keywords to attribute names (as strings)
    
    for key, value in mapping.items():
        if key in comp_lower:
            # Use getattr safely, raise error if missing
            attr_name = value[0]
            if hasattr(net, attr_name):
                return getattr(net, attr_name)
            else:
                raise AttributeError(f"The network has no component '{attr_name}'")

def connect_field_combo_box_to_layer(layer_combo_box,field_combo_box):
    layer_combo_box.layerChanged.connect(
         lambda layer, fc=field_combo_box: fc.setLayer(layer if layer and layer.type() == QgsMapLayer.VectorLayer else None)
         )

def run_pipeflow(layers,
                 fluid,
                 args,
                 load_layers):
    
    net = on_create_network_clicked(components=layers,selected_fluid=fluid)

    print(net)

    pandapipes.pipeflow(
        net=net,
        **args
    )

    result_layers = [] 

    for layer in layers:
        if type(layer) != QgsVectorLayer:
            layer = QgsProject.instance().mapLayersByName(layer)[0]
        else:
            layer = layer

        layer_component = return_network_component_type(component_layer=layer)

        component_df = return_network_component(net=net, component=layer.name())

        component_result_df = return_component_result(net=net,component=layer.name())

        component_result_df['name'] = component_df['name']

        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Define new folder name and path
        new_folder_name = 'working'
        new_folder_path = os.path.join(script_dir, new_folder_name)

        # Create the folder if it doesn't exist
        os.makedirs(new_folder_path, exist_ok=True)

        component_file = os.path.join(new_folder_path, f'{layer_component}.csv')
        component_result_df.to_csv(component_file,index=False)

        uri = f"file:///{component_file}?delimiter=,&detectTypes=yes&geomType=none"

        results_layer = QgsVectorLayer(uri, f'{layer_component}','delimitedtext')

        merged_layer =  processing.run("native:joinattributestable", 
                                       {'INPUT':layer,
                                        'FIELD':'name',
                                        'INPUT_2':results_layer,
                                        'FIELD_2':'name',
                                        'FIELDS_TO_COPY':[],
                                        'METHOD':1,
                                        'DISCARD_NONMATCHING':False,
                                        'PREFIX':'',
                                        'OUTPUT':'memory:'})['OUTPUT']
        
        merged_layer = processing.run("native:deletecolumn", 
                                      {'INPUT':merged_layer,
                                       'COLUMN':['name_2'],
                                       'OUTPUT':'memory:'})['OUTPUT']

        if layer_component == "junction":

            script_directory = os.path.dirname(os.path.abspath(__file__))
            folder_path = os.path.join(script_directory, 'layer_styles')
            os.makedirs(folder_path, exist_ok=True)

            style_path = os.path.join(folder_path, 'junction_res_pres.qml')

            re_calc_graduated(layer=merged_layer, qml_path=style_path)

        if layer_component == "pipe":

            script_directory = os.path.dirname(os.path.abspath(__file__))
            folder_path = os.path.join(script_directory, 'layer_styles')
            os.makedirs(folder_path, exist_ok=True)

            style_path = os.path.join(folder_path, 'pipe_res_pres.qml')

            re_calc_graduated(layer=merged_layer, qml_path=style_path)   

        merged_layer.setName(f'{layer.name()} Results')

        if load_layers:
            QgsProject.instance().addMapLayer(merged_layer)

        result_layers.append(merged_layer)

    return result_layers
    

