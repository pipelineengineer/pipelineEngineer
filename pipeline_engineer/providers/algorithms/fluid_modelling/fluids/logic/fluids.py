import os
import processing

from qgis.core import (QgsVectorLayer,QgsField,QgsFields,QgsFeature,QgsGeometry,QgsPointXY,QgsProject)

import pandapipes as pp
import pandas as pd

try:
    import xlsxwriter
    excel_available = True
except:
    excel_available = False

def get_fluid_parameter(parameter,chosen_fluid,temperature,pressure):
    pres = float(pressure)
    temp = float(temperature)

    fluid_properties = []

    net = pp.create_empty_network(fluid=f"{chosen_fluid}")
    
    if parameter == 'compressibility':
        value = net.fluid.get_compressibility(pres)
        
    elif parameter == 'density':
        value = net.fluid.get_density(temp)
        
    elif parameter == 'heat_capacity':
        value = net.fluid.get_heat_capacity(temp)
        
    elif parameter == 'molar_mass':
        value = net.fluid.get_molar_mass(temp)
        
    elif parameter == 'viscosity':
        value = net.fluid.get_viscosity(temp)
        
    else:
        print('Parameter not available. Check spelling.')
        return
    
    return value

def add_fluid_params_to_layer(layer,chosen_fluid,parameter,temperature,pressure,add_fluid):
    
    parameter_value = get_fluid_parameter(parameter=parameter,
                                          chosen_fluid=chosen_fluid,
                                          temperature=temperature,
                                          pressure=pressure)

    if add_fluid:
        print(chosen_fluid)
    
        layer = processing.run("native:fieldcalculator", 
                                        {'INPUT':layer,
                                         'FIELD_NAME':'fluid',
                                         'FIELD_TYPE':2, #text
                                         'FIELD_LENGTH':0,
                                         'FIELD_PRECISION':0,
                                         'FORMULA':f'\'{chosen_fluid}\'',
                                         'OUTPUT':'memory:'})['OUTPUT']

    parameter_added = processing.run("native:fieldcalculator", 
                                            {'INPUT':layer,
                                             'FIELD_NAME':parameter,
                                             'FIELD_TYPE':0, #decimal
                                             'FIELD_LENGTH':0,
                                             'FIELD_PRECISION':0,
                                             'FORMULA':f'{parameter_value}',
                                             'OUTPUT':'memory:'})['OUTPUT']

    parameter_added.setName(f'{parameter.capitalize()} Added')
    
    return parameter_added

