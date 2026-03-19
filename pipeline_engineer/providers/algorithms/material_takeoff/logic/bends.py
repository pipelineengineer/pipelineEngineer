import os
import processing

import pandas as pd

from qgis.core import QgsProject, QgsVectorLayer, QgsMapLayer


def summarise_bends(layer,id_field,min_bend_angle,feature_id_exp):
    exploded_lines = processing.run("native:explodelines", 
                                    {'INPUT':layer,
                                     'OUTPUT':'memory:'})['OUTPUT']
    
    angles_added = processing.run("native:fieldcalculator", 
                                  {'INPUT':exploded_lines,
                                   'FIELD_NAME':'angle',
                                   'FIELD_TYPE':0,
                                   'FIELD_LENGTH':0,
                                   'FIELD_PRECISION':0,
                                   'FORMULA':' angle_at_vertex($geometry,0)',
                                   'OUTPUT':'memory:'})['OUTPUT']
    
    line_intersections = processing.run("native:lineintersections", 
                                        {'INPUT':angles_added,
                                         'INTERSECT':angles_added,
                                         'INPUT_FIELDS':[id_field,'angle'],
                                         'INTERSECT_FIELDS':[id_field,'angle'],
                                         'INTERSECT_FIELDS_PREFIX':'',
                                         'OUTPUT':'memory:'})['OUTPUT']

    angle_delta = processing.run("native:fieldcalculator", 
                                 {'INPUT':line_intersections,
                                  'FIELD_NAME':'angle_delta',
                                  'FIELD_TYPE':0,
                                  'FIELD_LENGTH':0,
                                  'FIELD_PRECISION':0,
                                  'FORMULA':'ABS("angle"-"angle_2")',
                                  'OUTPUT':'memory:'})['OUTPUT']
    
    bends_within_straights = processing.run("native:extractbyexpression", 
                                            {'INPUT':angle_delta,
                                             'EXPRESSION':f'"{id_field}" = "{id_field}_2"',
                                             'OUTPUT':'memory:'})['OUTPUT']
    
    duplicates_removed = processing.run("native:deleteduplicategeometries", 
                                {'INPUT':bends_within_straights,
                                 'OUTPUT':'memory:'})['OUTPUT']
    
    dropped = processing.run("native:retainfields", 
                             {'INPUT':duplicates_removed,
                              'FIELDS':[id_field,'angle_delta'],
                              'OUTPUT':'memory:'})['OUTPUT']
    
    table_renamed = processing.run("native:renametablefield", 
                                   {'INPUT':dropped,
                                    'FIELD':'angle_delta',
                                    'NEW_NAME':'angle',
                                    'OUTPUT':'memory:'})['OUTPUT']
    
    corridor_renamed = processing.run("native:renametablefield", 
                                   {'INPUT':table_renamed,
                                    'FIELD':id_field,
                                    'NEW_NAME':'corridor',
                                    'OUTPUT':'memory:'})['OUTPUT']
    
    small_bends_removed = processing.run("native:extractbyexpression", 
                                         {'INPUT':corridor_renamed,
                                          'EXPRESSION':f'"angle" > {min_bend_angle} AND "angle" <= 95',
                                          'OUTPUT':'memory:'})['OUTPUT']
    
    id_field_added = processing.run("native:fieldcalculator", 
                                    {'INPUT':small_bends_removed,
                                     'FIELD_NAME':'feat_id',
                                     'FIELD_TYPE':2,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':feature_id_exp,
                                     'OUTPUT':'memory:'})['OUTPUT']

    refactored = processing.run("native:refactorfields", 
                                    {'INPUT':id_field_added,
                                     'FIELDS_MAPPING':[
                                                        {'alias': '','comment': '','expression': '"feat_id"','length': 0,'name': 'feat_id','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                                        {'alias': '','comment': '','expression': '"angle"','length': 0,'name': 'angle','precision': 0,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                                                        {'alias': '','comment': '','expression': '"corridor"','length': 255,'name': 'corridor','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'}
                                                       ],
                                     'OUTPUT':'memory:'})['OUTPUT']
    
    return refactored