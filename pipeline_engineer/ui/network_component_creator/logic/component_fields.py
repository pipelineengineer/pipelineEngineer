from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsField
from qgis.PyQt.QtCore import Qt, QVariant
import pandapipes

from .function_helpers import *

component_fields_dict = { "Junction": ['pn_bar','tfluid_k', 'height_m','name', 
                                       'in_service','type','geodata'],
                         
                           "Pipe":['from_junction', 'to_junction', 'length_km', 
                                   'diameter_m', 'k_mm', 'loss_coefficient', 
                                 'sections', 'alpha_w_per_m2k', 'text_k', 'qext_w', 
                                 'name', 'geodata', 'in_service', 'type'],

                           "Valve":['from_junction', 'to_junction', 'diameter_m',
                                    'opened', 'loss_coefficient', 'name', 
                                    'type'], 

                           "Sink":['junction', 'mdot_kg_per_s', 'scaling',
                                   'name', 'in_service', 'type'],

                           "Source":['junction', 'mdot_kg_per_s', 'scaling',
                                     'name', 'in_service', 'type'],

                           "Mass Storage":['junction', 'mdot_kg_per_s', 'init_m_stored_kg',
                                           'min_m_stored_kg', 'max_m_stored_kg', 'scaling','name', 
                                           'index', 'in_service', 'type'],

                           "External Grid":['junction', 'p_bar', 't_k', 'type',
                                            'name', 'in_service'],

                           "Heat Exchanger":['from_junction', 'to_junction', 'qext_w',
                                             'loss_coefficient', 'name', 
                                             'in_service','type'],

                           "Pump":['from_junction', 'to_junction', 'std_type',
                                   'name', 'in_service', 'type'],

                           "Circulation Pump Mass":['return_junction', 'flow_junction', 
                                                    'p_flow_bar','mdot_flow_kg_per_s', 't_flow_k', 
                                                    'name','in_service', 'type'],

                           "Circulation Pump Pressure":['return_junction', 'flow_junction', 
                                                        'p_flow_bar','plift_bar', 't_flow_k', 'type', 
                                                        'name','in_service'],

                           "Compressor":['from_junction', 'to_junction', 
                                         'pressure_ratio','name', 
                                         'in_service'],

                           "Pressure Control":['from_junction', 'to_junction', 
                                               'controlled_junction','controlled_p_bar', 
                                               'control_active', 'loss_coefficient','name', 
                                               'index', 'in_service', 'type'],

                           "Flow Control":['from_junction', 'to_junction', 'controlled_mdot_kg_per_s',
                                           'control_active', 'name', 
                                           'in_service', 'type'] }


component_geometries_dict = {
    "Junction": ['Point'],

    "Pipe":['LineString'],

    "Valve":['Point','LineString','Polygon'],

    "Sink":['Point','LineString','Polygon'],

    "Source":['Point','LineString','Polygon'],

    "Mass Storage":['Point','LineString','Polygon'],

    "External Grid":['Point','LineString','Polygon'],

    "Heat Exchanger":['Point','LineString','Polygon'],

    "Pump":['Point','LineString','Polygon'],

    "Circulation Pump Mass":['Point','LineString','Polygon'],

    "Circulation Pump Pressure":['Point','LineString','Polygon'],

    "Compressor":['Point','LineString','Polygon'],

    "Pressure Control":['Point','LineString','Polygon'],

    "Flow Control":['Point','LineString','Polygon']
                    }

field_types = fields = [
    QgsField("controlled_junction", QVariant.String),
    QgsField("controlled_mdot_kg_per_s", QVariant.Double),
    QgsField("controlled_p_bar", QVariant.Double),
    QgsField("control_active", QVariant.Bool),
    QgsField("diameter_m", QVariant.Double),
    QgsField("flow_junction", QVariant.String),
    QgsField("from_junction", QVariant.String),
    QgsField("geodata", QVariant.String),
    QgsField("height_m", QVariant.Double),
    QgsField("in_service", QVariant.Bool),
    QgsField("init_m_stored_kg", QVariant.Double),
    QgsField("k_mm", QVariant.Double),
    QgsField("length_km", QVariant.Double),
    QgsField("loss_coefficient", QVariant.Double),
    QgsField("max_m_stored_kg", QVariant.Double),
    QgsField("mdot_flow_kg_per_s", QVariant.Double),
    QgsField("mdot_kg_per_s", QVariant.Double),
    QgsField("min_m_stored_kg", QVariant.Double),
    QgsField("name", QVariant.String),
    QgsField("net", QVariant.String),
    QgsField("opened", QVariant.Bool),
    QgsField("pn_bar", QVariant.Double),
    QgsField("p_bar", QVariant.Double),
    QgsField("p_flow_bar", QVariant.Double),
    QgsField("alpha_w_per_m2k", QVariant.Double),
    QgsField("plift_bar", QVariant.Double),
    QgsField("pressure_ratio", QVariant.Double),
    QgsField("qext_w", QVariant.Double),
    QgsField("return_junction", QVariant.String),
    QgsField("scaling", QVariant.Double),
    QgsField("sections", QVariant.Int),
    QgsField("std_type", QVariant.String),
    QgsField("t_flow_k", QVariant.Double),
    QgsField("t_k", QVariant.Double),
    QgsField("text_k", QVariant.Double),
    QgsField("tfluid_k", QVariant.Double),
    QgsField("to_junction", QVariant.String),
    QgsField("type", QVariant.String),
    QgsField("u_w_per_m2k", QVariant.Double),
    QgsField("kwargs", QVariant.String),
    QgsField("junction", QVariant.String),
]

def create_junction_layer_from_existing(layer,fields_to_keep):
    network_vertices = processing.run("native:extractspecificvertices", 
                                        {'INPUT':layer,
                                        'VERTICES':'0,-1',
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    delete_dupes = processing.run("native:deleteduplicategeometries", 
                                    {'INPUT':network_vertices,
                                    'OUTPUT':'memory:'})['OUTPUT']

    name_added = processing.run("native:fieldcalculator", 
                                {'INPUT':delete_dupes,
                                    'FIELD_NAME':'name',
                                    'FIELD_TYPE':2, # Text
                                    'FIELD_LENGTH':0,
                                    'FIELD_PRECISION':0,
                                    'FORMULA':"CONCAT('Junction ',$id)",
                                    'OUTPUT':'memory:'})['OUTPUT']
    
    fields_to_keep.append('name')

    dropped = processing.run("native:retainfields", 
                            {'INPUT':name_added,
                            'FIELDS':fields_to_keep,
                            'OUTPUT':'memory:'})['OUTPUT']

    QgsProject.instance().addMapLayer(dropped)

    return dropped

def create_pipe_layer_from_existing(layer,fields_to_keep,junction_layer,component_name_field):
    layer = processing.run("native:renametablefield", 
            {'INPUT':layer,
            'FIELD':component_name_field,
            'NEW_NAME':'name',
            'OUTPUT':'memory:'})['OUTPUT']

    from_vertices = processing.run("native:extractspecificvertices", 
                                        {'INPUT':layer,
                                        'VERTICES':'0',
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    attach_from_node_id = processing.run("native:joinattributesbylocation", 
                                            {'INPUT':from_vertices,
                                            'PREDICATE':[2], # Equals
                                            'JOIN':junction_layer,
                                            'JOIN_FIELDS':['name'],
                                            'METHOD':0,
                                            'DISCARD_NONMATCHING':False,
                                            'PREFIX':'',
                                            'OUTPUT':'memory:'})['OUTPUT']
    
    rename_from = processing.run("native:renametablefield", 
                                    {'INPUT':attach_from_node_id,
                                    'FIELD':'name_2',
                                    'NEW_NAME':'from_junction',
                                    'OUTPUT':'memory:'})['OUTPUT']
    
    to_vertices = processing.run("native:extractspecificvertices", 
                                        {'INPUT':layer,
                                        'VERTICES':'-1',
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    attach_to_node_id = processing.run("native:joinattributesbylocation", 
                                            {'INPUT':to_vertices,
                                            'PREDICATE':[2], # Equals
                                            'JOIN':junction_layer,
                                            'JOIN_FIELDS':['name'],
                                            'METHOD':0,
                                            'DISCARD_NONMATCHING':False,
                                            'PREFIX':'',
                                            'OUTPUT':'memory:'})['OUTPUT']
    
    rename_to = processing.run("native:renametablefield", 
                                    {'INPUT':attach_to_node_id,
                                    'FIELD':'name_2',
                                    'NEW_NAME':'to_junction',
                                    'OUTPUT':'memory:'})['OUTPUT']
    
    join_from_jct = processing.run("native:joinattributestable", 
                                    {'INPUT':layer,
                                        'FIELD':'name',
                                        'INPUT_2':rename_from,
                                        'FIELD_2':'name',
                                        'FIELDS_TO_COPY':['from_junction'],
                                        'METHOD':1,
                                        'DISCARD_NONMATCHING':False,
                                        'PREFIX':'',
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    join_to_jct = processing.run("native:joinattributestable", 
                                    {'INPUT':join_from_jct,
                                        'FIELD':'name',
                                        'INPUT_2':rename_to,
                                        'FIELD_2':'name',
                                        'FIELDS_TO_COPY':['to_junction'],
                                        'METHOD':1,
                                        'DISCARD_NONMATCHING':False,
                                        'PREFIX':'',
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    fields_to_keep.extend(['name','from_junction','to_junction'])

    dropped = processing.run("native:retainfields", 
                                {'INPUT':join_to_jct,
                                'FIELDS':fields_to_keep,
                                'OUTPUT':'memory:'})['OUTPUT']

    return dropped
            
def create_component_with_junctions_from_existing(layer,fields_to_keep,component_name_field,junction_layer):
        layer = processing.run("native:renametablefield", 
                                        {'INPUT':layer,
                                        'FIELD':component_name_field,
                                        'NEW_NAME':'name',
                                        'OUTPUT':'memory:'})['OUTPUT']

        nearest_joined = processing.run("native:joinbynearest", 
                                        {'INPUT':layer,
                                        'INPUT_2':junction_layer,
                                        'FIELDS_TO_COPY':['name'],
                                        'DISCARD_NONMATCHING':False,
                                        'PREFIX':'',
                                        'NEIGHBORS':1,
                                        'MAX_DISTANCE':None,
                                        'OUTPUT':'memory:'})['OUTPUT']
        
        rename_jct = processing.run("native:renametablefield", 
                                        {'INPUT':nearest_joined,
                                        'FIELD':'name_2',
                                        'NEW_NAME':'junction',
                                        'OUTPUT':'memory:'})['OUTPUT']
        
        fields_to_keep.extend(['name','junction'])

        dropped = processing.run("native:retainfields", 
                                    {'INPUT':rename_jct,
                                    'FIELDS':fields_to_keep,
                                    'OUTPUT':'memory:'})['OUTPUT']
        
        return dropped

def create_component_from_existing(layer,component_name_field,fields_to_keep):
    layer = processing.run("native:renametablefield", 
                                        {'INPUT':layer,
                                        'FIELD':component_name_field,
                                        'NEW_NAME':'name',
                                        'OUTPUT':'memory:'})['OUTPUT']


    dropped = processing.run("native:retainfields", 
                                {'INPUT':layer,
                                'FIELDS':fields_to_keep,
                                'OUTPUT':'memory:'})['OUTPUT']
    
    return dropped

def add_fields_through_provider(layer,fields,junction_layer):
    # 3. Add the fields to the memory layer
    provider = layer.dataProvider()
    provider.addAttributes(fields)

    # 4. Update the layer’s fields so QGIS recognizes them
    layer.updateFields()

    junction_fields = ["junction","controlled_junction", "flow_junction", "from_junction", "return_junction", "to_junction"]

    common_values = set(fields) & set(junction_fields)

    for value in common_values:
        setup_value_relation(layer=layer,field_name=value,junction_layer=junction_layer)