import os
import processing

from qgis.core import (QgsVectorLayer,QgsField,QgsFields,QgsFeature,QgsGeometry,QgsPointXY,QgsProject, QgsMapLayer)

import pandas as pd
import pandapower

mapping_pandapower = {
    "Bus": ["bus", "res_bus", pandapower.create_bus, None],
    "Bus DC": ["bus_dc", "res_bus_dc", pandapower.create_bus, None],
    "Line": ["line", "res_line", pandapower.create_line, None],
    "Line DC": ["line_dc", "res_line_dc", pandapower.create_line, None],
    "Switch": ["switch", "res_switch", pandapower.create_switch, None],
    "Load": ["load", "res_load", pandapower.create_load, None],
    "Load DC": ["load_dc", "res_load_dc", pandapower.create_load, None],
    "Asymmetric Load": ["asymmetric_load", "res_asymmetric_load", pandapower.create_asymmetric_load, None],
    "Motor": ["motor", "res_motor", pandapower.create_motor, None],
    "Static Generator": ["sgen", "res_sgen", pandapower.create_sgen, None],
    "Asymmetric Static Generator": ["asymmetric_sgen", "res_asymmetric_sgen", pandapower.create_asymmetric_sgen, None],
    "Generator": ["gen", "res_gen", pandapower.create_gen, None],
    "External Grid": ["ext_grid", "res_ext_grid", pandapower.create_ext_grid, None],
    "Source DC": ["source_dc", "res_source_dc", pandapower.create_ext_grid, None],
    "Transformer": ["trafo", "res_trafo", pandapower.create_transformer, None],
    "Three Winding Transformer": ["trafo3w", "res_trafo3w", pandapower.create_transformer3w, None],
    "Shunt": ["shunt", "res_shunt", pandapower.create_shunt, None],
    "Impedance": ["impedance", "res_impedance", pandapower.create_impedance, None],
    "Ward": ["ward", "res_ward", pandapower.create_ward, None],
    "Extended Ward": ["xward", "res_xward", pandapower.create_xward, None],
    #"HV DC Link / DC Line": ["hvdc", "res_hvdc", pandapower.create_hvdc, None],
    "Measurement": ["measurement", None, pandapower.create_measurement, None],
    "Storage": ["storage", "res_storage", pandapower.create_storage, None],
    "Static Var Compensator (SVC)": ["svc", "res_svc", pandapower.create_svc, None],
    "Thyristor-Controlled Series Capacitor (TCSC)": ["tcsc", "res_tcsc", pandapower.create_tcsc, None],
    "Static Synchronous Compensator (SSC)": ["ssc", "res_ssc", pandapower.create_ssc, None],
    "Voltage Source Converter (VSC)": ["vsc", "res_vsc", pandapower.create_vsc, None],
    "Stacked Voltage Source Converter (VSC Stacked)": ["vsc_stacked", "res_vsc_stacked", pandapower.create_vsc, None],
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
    
    component = component.replace(" Layer","")

    component_list = list(mapping_pandapower.keys())

    for item in component_list:
          
          if item in component:
                comp_key = item
                break
    
    component_type = mapping_pandapower[comp_key][0]

    return component_type

def create_component(component, arg):
    if not isinstance(component, str):
        component = component.name()

    comp_lower = component.lower()
    
    component = component.replace(" Layer","")

    # mapping_pandapower keywords to pandapipes creation functions

    # Find and call the correct function
    for key, value in mapping_pandapower.items():
        if key in component:
            func = value[2]
            
            print('FUNCTION: ',func)
            
            return func(**arg)  # Call the function with arguments

def on_create_network_clicked(components):

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
        if "bus" in lyr.name().lower():
            ordered_components.append(lyr)

    # pipes second
    for lyr in layers:
        if "line" in lyr.name().lower():
            ordered_components.append(lyr)

    # remaining components
    for lyr in layers:
        lname = lyr.name().lower()
        if "bus" not in lname and "line" not in lname:
            ordered_components.append(lyr)

    # Now the components list is clean
    components = ordered_components

    # ---------------------------------------------------------
    # CREATE NETWORK
    # ---------------------------------------------------------
    net = pandapower.create_empty_network()

    # Track junction table (needed for mapping_pandapower)
    bus_df = None

    # ---------------------------------------------------------
    # ADD COMPONENTS
    # ---------------------------------------------------------
    for layer in components:

        print("Processing layer:", layer.name())

        component_df = layer_to_df(layer)
        
        component_df_columns = component_df.columns.tolist()

        # Detect junction-related fields
        bus_fields = []

        for field in component_df_columns:
            
            if "bus" in field:
                bus_fields.append(field)

        common_values = set(component_df_columns) & set(bus_fields)

        # JUNCTION LAYER → create index
        if "bus" in layer.name().lower():
            component_df['index'] = component_df.index
            bus_df = component_df.copy()

        # OTHER COMPONENTS → map junction references to indexes
        elif bus_df is not None and common_values:
            for field in common_values:
                component_df[field] = component_df[field].map(
                    bus_df.set_index('name')['index']
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
            
            print(arg)

    return net


def return_component_result(net,component):
        if type(component) != str:
            component = component.name()

        #comp_lower = component.lower()

        comp_lower = component.replace(" Layer","")

        print(comp_lower)


        for key, value in mapping_pandapower.items():
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

    comp_lower = component.replace(" Layer","")
    
    # Map keywords to attribute names (as strings)
    
    for key, value in mapping_pandapower.items():
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

def run_dc_powerflow(layers,
                 load_layers):
    
    net = on_create_network_clicked(components=layers)

    print(net)

    pandapower.rundcpp(net=net)

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
        new_folder_name = 'power_working'
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

        if layer_component == "bus":

            script_directory = os.path.dirname(os.path.abspath(__file__))
            folder_path = os.path.join(script_directory, 'layer_styles')
            os.makedirs(folder_path, exist_ok=True)

            style_path = os.path.join(folder_path, 'power_bus_results.qml')

            re_calc_graduated(layer=merged_layer, qml_path=style_path)

        if layer_component == "line":

            script_directory = os.path.dirname(os.path.abspath(__file__))
            folder_path = os.path.join(script_directory, 'layer_styles')
            os.makedirs(folder_path, exist_ok=True)

            style_path = os.path.join(folder_path, 'power_line_results.qml')

            re_calc_graduated(layer=merged_layer, qml_path=style_path)   

        merged_layer.setName(f'{layer.name()} Results')

        if load_layers:
            QgsProject.instance().addMapLayer(merged_layer)

        result_layers.append(merged_layer)

    return result_layers
    

