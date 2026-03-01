import os
import processing

from qgis.core import QgsProject

def attach_pipe_attributes(point_layer,point_fields_containing_lines,
                            service, remove_line_service,
                           line_layer,line_id_field,line_attributes_to_copy):

    joined_layer = point_layer

    for field in point_fields_containing_lines:
        
        local_line_layer = line_layer
        
        attributes = []
        
        for line_attribute in line_attributes_to_copy:
            
            if remove_line_service:
                substring_to_remove =  service.replace(" ","_").lower()
                
                line_attribute_removed = line_attribute.replace(substring_to_remove+"_", "")
                
                line_attribute_updated = f'{field}_{line_attribute_removed}'
            else:
                line_attribute_updated = f'{field}_{line_attribute}'
            
            local_line_layer = processing.run("native:renametablefield", 
                                            {'INPUT':local_line_layer,
                                             'FIELD':line_attribute,
                                             'NEW_NAME':line_attribute_updated,
                                             'OUTPUT':'memory:'})['OUTPUT']

            attributes.append(line_attribute_updated)
        
        
        joined_layer = processing.run("native:joinattributestable", 
                                                    {'INPUT':joined_layer,
                                                     'FIELD':field,
                                                     'INPUT_2':local_line_layer,
                                                     'FIELD_2':line_id_field,
                                                     'FIELDS_TO_COPY':attributes,
                                                     'METHOD':1,
                                                     'DISCARD_NONMATCHING':False,
                                                     'PREFIX':'','OUTPUT':'memory:'})['OUTPUT']

    return joined_layer

    return joined_layer