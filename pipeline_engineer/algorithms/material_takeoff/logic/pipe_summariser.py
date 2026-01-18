import os
import processing

def pipe_summariser(layer,corridor_id_field,size_formula,class_formula,length_formula,material_formula,service):
    
    if corridor_id_field != 'corridor_id':
        corridor_id = processing.run("native:renametablefield", 
                                    {'INPUT':layer,
                                     'FIELD':corridor_id_field,
                                     'NEW_NAME':'corridor_id',
                                     'OUTPUT':'memory:'})['OUTPUT']
        
    else:
        corridor_id = layer
    
    service_lower = service.replace(" ","_").lower()
    
    material = processing.run("native:fieldcalculator", 
                                    {'INPUT':corridor_id,
                                     'FIELD_NAME':f'{service_lower}_material',
                                     'FIELD_TYPE':2,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':material_formula,
                                     'OUTPUT':'memory:'})['OUTPUT']
    
    line_size = processing.run("native:fieldcalculator", 
                                    {'INPUT':material,
                                     'FIELD_NAME':f'{service_lower}_size',
                                     'FIELD_TYPE':0,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':size_formula,
                                     'OUTPUT':'memory:'})['OUTPUT']

    line_class = processing.run("native:fieldcalculator", 
                                    {'INPUT':line_size,
                                     'FIELD_NAME':f'{service_lower}_class',
                                     'FIELD_TYPE':0,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':class_formula,
                                     'OUTPUT':'memory:'})['OUTPUT']

    line_length = processing.run("native:fieldcalculator", 
                                    {'INPUT':line_class,
                                     'FIELD_NAME':f'{service_lower}_length',
                                     'FIELD_TYPE':0,
                                     'FIELD_LENGTH':0,
                                     'FIELD_PRECISION':0,
                                     'FORMULA':length_formula,
                                     'OUTPUT':'memory:'})['OUTPUT']

    retained = processing.run("native:retainfields", 
                                    {'INPUT':line_length,
                                     'FIELDS':['corridor_id',f'{service_lower}_material',f'{service_lower}_size',f'{service_lower}_class',f'{service_lower}_length'],
                                     'OUTPUT':'memory:'})['OUTPUT']

    retained.setName(f'{service} Summary Table')

    return retained