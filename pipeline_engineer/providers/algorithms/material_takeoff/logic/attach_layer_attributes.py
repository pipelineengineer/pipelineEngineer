import os
import processing

from qgis.core import QgsProject, QgsVectorLayer, QgsMapLayer

def attach_layer_attributes(attribute_layer,attribute_layer_field,layer_to_be_attributed,fields_containing_attributes,attributes_to_copy):
    
    print(attribute_layer.name())
    print(layer_to_be_attributed.name())
    
    for field in fields_containing_attributes:
        
        local_attributes_to_copy = []
        
        local_attribute_layer = attribute_layer
        
        for attr_field in attributes_to_copy:
            
            field_name = f'{field}_{attr_field}'
            local_attributes_to_copy.append(field_name)
            
            local_attribute_layer = processing.run("native:renametablefield", 
                                    {'INPUT':local_attribute_layer,
                                     'FIELD':attr_field,
                                     'NEW_NAME':field_name,
                                     'OUTPUT':'memory:'})['OUTPUT']
        
        
        layer_to_be_attributed = processing.run("native:joinattributestable", 
                                                    {'INPUT':layer_to_be_attributed,
                                                     'FIELD':field,
                                                     'INPUT_2':local_attribute_layer,
                                                     'FIELD_2':attribute_layer_field,
                                                     'FIELDS_TO_COPY':local_attributes_to_copy,
                                                     'METHOD':1,
                                                     'DISCARD_NONMATCHING':False,
                                                     'PREFIX':'',
                                                     'OUTPUT':'memory:'})['OUTPUT']

    return layer_to_be_attributed