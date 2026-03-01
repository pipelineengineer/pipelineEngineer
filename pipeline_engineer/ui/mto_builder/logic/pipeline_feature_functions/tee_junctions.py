import os
import processing

import pandas as pd

from qgis.core import QgsProject, QgsVectorLayer, QgsMapLayer

def summarise_tees(layer,id_field,id_expression):
    if type(layer) == QgsVectorLayer:
        layer = layer
    else:
        layer = QgsProject.instance().mapLayersByName(layer)[0]

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
    
    joined = processing.run("native:joinattributesbylocation", 
                            {'INPUT':line_intersections,
                             'PREDICATE':[2], # Equals
                             'JOIN':line_intersections,
                             'JOIN_FIELDS':[id_field,'angle'],
                             'METHOD':0,
                             'DISCARD_NONMATCHING':False,
                             'PREFIX':'',
                             'OUTPUT':'memory:'})['OUTPUT']
    
    extract_unique_junctions = processing.run("native:extractbyexpression", 
                                           {'INPUT':joined,
                                            'EXPRESSION':f'"{id_field}" != "{id_field}_2" AND "{id_field}" != "{id_field}_3" AND "{id_field}_2" != "{id_field}_3" ',
                                            'OUTPUT':'memory:'})['OUTPUT']
    
    extract_branch_first = processing.run("native:extractbyexpression", 
                                          {'INPUT':extract_unique_junctions,
                                           'EXPRESSION':'ABS("angle" - "angle_2") > ABS("angle_2"-"angle_3") AND ABS("angle" - "angle_3") > ABS("angle_2"-"angle_3") ',
                                           'OUTPUT':'memory:'})['OUTPUT']
    
    dupes_deleted = processing.run("native:deleteduplicategeometries", 
                                   {'INPUT':extract_branch_first,
                                    'OUTPUT':'memory:'})['OUTPUT']
    
    branch_named = processing.run("native:renametablefield", 
            {'INPUT':dupes_deleted,
            'FIELD':id_field,
            'NEW_NAME':'branch',
            'OUTPUT':'memory:'})['OUTPUT']

    header_named = processing.run("native:renametablefield", 
            {'INPUT':branch_named,
            'FIELD':f'{id_field}_2',
            'NEW_NAME':'header_1',
            'OUTPUT':'memory:'})['OUTPUT']
    
    header_sec_named = processing.run("native:renametablefield", 
            {'INPUT':header_named,
            'FIELD':f'{id_field}_3',
            'NEW_NAME':'header_2',
            'OUTPUT':'memory:'})['OUTPUT']
    
    branch_angle_added = processing.run("native:fieldcalculator", 
                                    {'INPUT':header_sec_named,
                                     'FIELD_NAME':'branch_angle',
                                     'FIELD_TYPE':0,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':'MAX("angle","angle_2")-MIN("angle","angle_2")',
                                     'OUTPUT':'memory:'})['OUTPUT']
    
    dropped = processing.run("native:retainfields", 
                                {'INPUT':branch_angle_added,
                                'FIELDS':['branch','header_1','header_2','branch_angle'],
                                'OUTPUT':'memory:'})['OUTPUT']

    id_field_added = processing.run("native:fieldcalculator", 
                                    {'INPUT':dropped,
                                     'FIELD_NAME':'feat_id',
                                     'FIELD_TYPE':2,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':id_expression,
                                     'OUTPUT':'memory:'})['OUTPUT']

    refactored = processing.run("native:refactorfields", 
                                    {'INPUT':id_field_added,
                                     'FIELDS_MAPPING':[
                                                        {'alias': '','comment': '','expression': '"feat_id"','length': 0,'name': 'feat_id','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                                        {'alias': '','comment': '','expression': '"branch_angle"','length': 0,'name': 'branch_angle','precision': 0,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                                                        {'alias': '','comment': '','expression': '"branch"','length': 255,'name': 'branch','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                                        {'alias': '','comment': '','expression': '"header_1"','length': 255,'name': 'header_1','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                                        {'alias': '','comment': '','expression': '"header_2"','length': 255,'name': 'header_2','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'}
                                                       ],
                                      'OUTPUT':'memory:'})['OUTPUT']

    return refactored