import os
import processing

import pandas as pd

from qgis.core import QgsProject, QgsVectorLayer, QgsMapLayer

def summarise_four_way_unions(layer,id_field,id_expression):
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
    
    joined_two = processing.run("native:joinattributesbylocation", 
                            {'INPUT':joined,
                             'PREDICATE':[2], # Equals
                             'JOIN':joined,
                             'JOIN_FIELDS':[id_field,'angle'],
                             'METHOD':0,
                             'DISCARD_NONMATCHING':False,
                             'PREFIX':'',
                             'OUTPUT':'memory:'})['OUTPUT']
    
    extract_unique_junctions = processing.run("native:extractbyexpression", 
                                           {'INPUT':joined_two,
                                            'EXPRESSION': (
                                                            f'"{id_field}" != "{id_field}_2" AND '
                                                            f'"{id_field}" != "{id_field}_3" AND '
                                                            f'"{id_field}" != "{id_field}_4" AND '
                                                            f'"{id_field}_2" != "{id_field}_3" AND '
                                                            f'"{id_field}_2" != "{id_field}_4" AND '
                                                            f'"{id_field}_3" != "{id_field}_4"'
                                                        ),
                                            'OUTPUT':'memory:'})['OUTPUT']
    
    dupes_deleted = processing.run("native:deleteduplicategeometries", 
                                   {'INPUT':extract_unique_junctions,
                                    'OUTPUT':'memory:'})['OUTPUT']
    
    branch_named = processing.run("native:renametablefield", 
            {'INPUT':dupes_deleted,
            'FIELD':id_field,
            'NEW_NAME':'branch_1',
            'OUTPUT':'memory:'})['OUTPUT']

    header_named = processing.run("native:renametablefield", 
            {'INPUT':branch_named,
            'FIELD':f'{id_field}_2',
            'NEW_NAME':'branch_2',
            'OUTPUT':'memory:'})['OUTPUT']
    
    header_sec_named = processing.run("native:renametablefield", 
            {'INPUT':header_named,
            'FIELD':f'{id_field}_3',
            'NEW_NAME':'branch_3',
            'OUTPUT':'memory:'})['OUTPUT']
    
    header_thr_named = processing.run("native:renametablefield", 
            {'INPUT':header_sec_named,
            'FIELD':f'{id_field}_4',
            'NEW_NAME':'branch_4',
            'OUTPUT':'memory:'})['OUTPUT']
    
    dropped = processing.run("native:retainfields", 
                                {'INPUT':header_thr_named,
                                'FIELDS':['branch_1','branch_2','branch_3','branch_4'],
                                'OUTPUT':'memory:'})['OUTPUT']
    
    id_field_added = processing.run("native:fieldcalculator", 
                                    {'INPUT':dropped,
                                     'FIELD_NAME':'feature',
                                     'FIELD_TYPE':2,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':id_expression,
                                     'OUTPUT':'memory:'})['OUTPUT']

    refactored = processing.run("native:refactorfields", 
                                    {'INPUT':id_field_added,
                                     'FIELDS_MAPPING':[
                                                        {'alias': '','comment': '','expression': '"feature"','length': 0,'name': 'feature','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                                        {'alias': '','comment': '','expression': '"branch_1"','length': 255,'name': 'branch_1','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                                        {'alias': '','comment': '','expression': '"branch_2"','length': 255,'name': 'branch_2','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                                        {'alias': '','comment': '','expression': '"branch_3"','length': 255,'name': 'branch_3','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                                                        {'alias': '','comment': '','expression': '"branch_4"','length': 255,'name': 'branch_4','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'}
                                                       ],
                                     'OUTPUT':'memory:'})['OUTPUT']

    return refactored