import os
import processing

from qgis.core import QgsProject

def summarise_points(point_layer,point_id_formula,
                     join_to_line_layer,
                     line_layer,line_id_field,
                     fields_to_retain,service,assembly_formula):

    point_layer_name = point_layer.name()

    point_layer = processing.run("native:fieldcalculator", 
                                    {'INPUT':point_layer,
                                     'FIELD_NAME':'feat_id',
                                     'FIELD_TYPE':2,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':point_id_formula,
                                     'OUTPUT':'memory:'})['OUTPUT']

    service_field = processing.run("native:fieldcalculator", 
                                    {'INPUT':point_layer,
                                     'FIELD_NAME':'service',
                                     'FIELD_TYPE':2,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':f'\'{service}\'',
                                     'OUTPUT':'memory:'})['OUTPUT']

    assy_field = processing.run("native:fieldcalculator", 
                                    {'INPUT':service_field,
                                     'FIELD_NAME':'assembly',
                                     'FIELD_TYPE':2,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':assembly_formula,
                                     'OUTPUT':'memory:'})['OUTPUT']

    fields_to_retain.extend(['feat_id','assembly','service'])

    if join_to_line_layer:
        if line_id_field != 'corridor':

            corridor = processing.run("native:renametablefield", 
                                            {'INPUT':line_layer,
                                             'FIELD':line_id_field,
                                             'NEW_NAME':'corridor',
                                             'OUTPUT':'memory:'})['OUTPUT']
          
        else:
            corridor = line_layer
        
        nearest_joined = processing.run("native:joinbynearest", 
                                        {'INPUT':assy_field,
                                        'INPUT_2':corridor,
                                        'FIELDS_TO_COPY':['corridor'],
                                        'DISCARD_NONMATCHING':False,
                                        'PREFIX':'',
                                        'NEIGHBORS':1,
                                        'MAX_DISTANCE':None,
                                        'OUTPUT':'memory:'})['OUTPUT']
        
        fields_to_retain.extend(['corridor'])
    
    else:
        nearest_joined = assy_field

    print(fields_to_retain)

    print(fields_to_retain)

    dropped = processing.run("native:retainfields", 
                            {'INPUT':nearest_joined,
                            'FIELDS':fields_to_retain,
                            'OUTPUT':'memory:'})['OUTPUT']
    
    dropped.setName(f'{point_layer_name} Summary')
    
    return dropped
