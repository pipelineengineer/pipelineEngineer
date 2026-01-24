import os
import sys
import processing

from qgis.core import (QgsVectorLayer,QgsField,QgsFields,QgsFeature,QgsGeometry,QgsPointXY,QgsProject,QgsProcessingFeedback,QgsProperty)

import pandapipes
import pandas as pd

# Get the parent folder (one level up from the current script)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)  # Add it to sys.path

from ...general_logic.function_helpers import *

def create_network_xyz_layer(pipe_results_layer,chainage,raster_layer,load_layers): 
    in_service_lines = processing.run("native:extractbyexpression", 
                                      {'INPUT':pipe_results_layer,
                                       'EXPRESSION':'"in_service" = TRUE',
                                       'OUTPUT':'memory:'})['OUTPUT']

    retained_fields = processing.run("native:retainfields", 
                                     {'INPUT':in_service_lines,
                                      'FIELDS':['name','from_junction','to_junction','length_km','diameter_m','k_mm','in_service','mdot_from_kg_per_s'],
                                      'OUTPUT':'memory:'})['OUTPUT']
    
    processing.run("qgis:selectbyexpression", {'INPUT':retained_fields,'EXPRESSION':'"mdot_from_kg_per_s" < 0','METHOD':0})

    lines_to_be_reversed = processing.run("native:saveselectedfeatures", 
                                            {'INPUT':retained_fields,
                                             'OUTPUT':'memory:'})['OUTPUT']
    
    retained_fields.invertSelection()

    other_lines = processing.run("native:saveselectedfeatures", 
                                            {'INPUT':retained_fields,
                                             'OUTPUT':'memory:'})['OUTPUT']

    reversed_lines = processing.run("native:reverselinedirection", 
                                        {'INPUT':lines_to_be_reversed,
                                         'OUTPUT':'memory:'})['OUTPUT']
    
    from_calc = processing.run("native:fieldcalculator", 
                                    {'INPUT':reversed_lines,
                                     'FIELD_NAME':'from_jct_calc',
                                     'FIELD_TYPE':2,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':'"to_junction"',
                                     'OUTPUT':'memory:'})['OUTPUT']

    to_calc = processing.run("native:fieldcalculator", 
                                    {'INPUT':from_calc,
                                     'FIELD_NAME':'to_jct_calc',
                                     'FIELD_TYPE':2,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':'"from_junction"',
                                     'OUTPUT':'memory:'})['OUTPUT']    
    
    flow_rate_calc =  processing.run("native:fieldcalculator", 
                                     {'INPUT':to_calc,
                                      'FIELD_NAME':'mdot_calc',
                                      'FIELD_TYPE':0,
                                      'FIELD_LENGTH':0,
                                      'FIELD_PRECISION':0,
                                      'FORMULA':'ABS( "mdot_from_kg_per_s" )',
                                      'OUTPUT':'memory:'})['OUTPUT']
    
    fields_dropped = processing.run("native:deletecolumn", 
                                    {'INPUT':flow_rate_calc,
                                     'COLUMN':['from_junction','to_junction','mdot_from_kg_per_s'],
                                     'OUTPUT':'memory:'})['OUTPUT']
    
    rename_one = processing.run("native:renametablefield", 
                                    {'INPUT':fields_dropped,
                                     'FIELD':'from_jct_calc',
                                     'NEW_NAME':'from_junction',
                                     'OUTPUT':'memory:'})['OUTPUT']
    
    rename_two = processing.run("native:renametablefield", 
                                    {'INPUT':rename_one,
                                     'FIELD':'to_jct_calc',
                                     'NEW_NAME':'to_junction',
                                     'OUTPUT':'memory:'})['OUTPUT']
    
    rename_three = processing.run("native:renametablefield", 
                                    {'INPUT':rename_two,
                                     'FIELD':'mdot_calc',
                                     'NEW_NAME':'mdot_from_kg_per_s',
                                     'OUTPUT':'memory:'})['OUTPUT']

    merged = processing.run("native:mergevectorlayers", 
                                    {'LAYERS':[other_lines,rename_three],
                                     'CRS':None,
                                     'OUTPUT':'memory:'})['OUTPUT']

    exp_extract = processing.run("native:extractbyexpression", 
                                        {'INPUT':merged,
                                         'EXPRESSION':'ABS("mdot_from_kg_per_s") >= 0.000001 AND "mdot_from_kg_per_s" IS NOT NULL',
                                         'OUTPUT':'memory:'})['OUTPUT']

    dropped_fields_lines = processing.run("native:deletecolumn", 
                                        {'INPUT':exp_extract,
                                         'COLUMN':['layer','path'],
                                         'OUTPUT':'memory:'})['OUTPUT']

    script_directory = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(script_directory, 'layer_styles')
    os.makedirs(folder_path, exist_ok=True)

    selected_style = 'pipe_skeleton_mass.qml'

    if selected_style:
        style_path = os.path.join(folder_path, selected_style)

        print(style_path)

        dropped_fields_lines.loadNamedStyle(style_path)
        dropped_fields_lines.triggerRepaint()

        re_calc_graduated(layer=dropped_fields_lines,qml_path=selected_style)

    # Checking Layer Measurement Units
    crs = dropped_fields_lines.crs()
    units = crs.mapUnits()

    print('UNITS: ',QgsUnitTypes.toString(units))

    divider = 1

    # XYZ Data
    if units != QgsUnitTypes.DistanceMeters:
        chainage = chainage/111111
        divider = 111111

    print(chainage)

    exp = f'CASE\r\nWHEN ($length / {divider}) < {chainage} THEN ($length/{divider})/3\r\nELSE {chainage}\r\nEND'
    
    print(exp)

    points_along_lines = processing.run("native:pointsalonglines", 
                                        {'INPUT':dropped_fields_lines,
                                        'DISTANCE':QgsProperty.fromExpression(exp),
                                        'START_OFFSET':0,
                                        'END_OFFSET':0,
                                        'OUTPUT':'memory:'})['OUTPUT']

    geom_fixed = processing.run("native:fixgeometries", 
                                        {'INPUT':points_along_lines,
                                         'METHOD':1,
                                         'OUTPUT':'memory:'})['OUTPUT']

    if units == QgsUnitTypes.DistanceDegrees:

        chainage_calculated = processing.run("native:fieldcalculator", 
                                            {'INPUT':geom_fixed,
                                            'FIELD_NAME':'chainage_m',
                                            'FIELD_TYPE':0,
                                            'FIELD_LENGTH':0,
                                            'FIELD_PRECISION':0,
                                            'FORMULA':'round("distance"*111111,0)',
                                            'OUTPUT':'memory:'})['OUTPUT']

    else:
        
        chainage_calculated = processing.run("native:fieldcalculator", 
                                            {'INPUT':geom_fixed,
                                            'FIELD_NAME':'chainage_m',
                                            'FIELD_TYPE':0,
                                            'FIELD_LENGTH':0,
                                            'FIELD_PRECISION':0,
                                            'FORMULA':'round("distance",0)',
                                            'OUTPUT':'memory:'})['OUTPUT']

    raster_sampling = processing.run("native:rastersampling", 
                                        {'INPUT':chainage_calculated,
                                        'RASTERCOPY':raster_layer,
                                        'COLUMN_PREFIX':'elev',
                                        'OUTPUT':'memory:'})['OUTPUT']

    dropped_fields = processing.run("native:deletecolumn", 
                                        {'INPUT':raster_sampling,
                                        'COLUMN':['distance','angle'],
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    dropped_fields_two = processing.run("native:deletecolumn", 
                                        {'INPUT':dropped_fields,
                                        'COLUMN':['layer','path'],
                                        'OUTPUT':'memory:'})['OUTPUT']

    selected_style = 'xyz_style_two.qml'

    if selected_style:
        style_path = os.path.join(folder_path, selected_style)

        print(style_path)

        dropped_fields_two.loadNamedStyle(style_path)
        dropped_fields_two.triggerRepaint()

        re_calc_graduated(layer=dropped_fields_two,qml_path=selected_style)


    if load_layers:
        dropped_fields_two.setName('Skeleton XYZ Data')
        QgsProject.instance().addMapLayer(dropped_fields_two)
        dropped_fields_lines.setName('Network Skeleton')
        QgsProject.instance().addMapLayer(dropped_fields_lines)

    return dropped_fields_two, dropped_fields_lines