import pandas as pd

import math

#from .function_helpers import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#specifications_path = os.path.join(BASE_DIR, 'pipe_data', 'specifications.xlsx')

specifications_path = 'C:/Users/tsura/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/mto_builder/logic/pipe_data/specifications.xlsx'

pipe_df = pd.read_excel(specifications_path,sheet_name='Pipe Assigner')

def pipe_size_nominator(row, v_target, rho, mu, pres_drop_per_m):
    
    #line_roughness = row['k_mm']
    
    pipe_length = row['sizer_length_field']
    
    friction_factor = 0.012

    friction_loss = pipe_length * pres_drop_per_m

    d = (friction_factor * rho * (v_target**2))/(2*friction_loss)

    #velocity_actual = vol_flow_rate_m_3_per_s / (math.pi *((d/2)**2))

    #reynolds_no = (rho * velocity_actual * d)/ mu

    #friction_factor = ( 0.25 / ((math.log10((line_roughness/(3700*d))+(5.74/(reynolds_no**0.9))))**2))

    #friction_loss = (friction_factor * rho * (velocity_actual**2))/(2*d)
    
    return d

def system_sizer(system_df,system_rating_bar,target_velocity,rho,mu,pres_drop_per_m):
    
    # Nominating Pipe Size
    system_df['nominal_size'] = system_df.apply(pipe_size_nominator, axis=1, args=(target_velocity,rho,mu,pres_drop_per_m))
    
    # System Sizer
    
    system_rated_df = pipe_df[pipe_df['pres_rating_bar'] == system_rating_bar]

    system_df['internal_diam'] = pd.to_numeric(system_df['nominal_size'], errors='coerce')
    system_rated_df['internal_diam'] = pd.to_numeric(system_rated_df['internal_diam'], errors='coerce')

    system_rated_df = system_rated_df.sort_values(by='internal_diam')
    system_df = system_df.sort_values(by='internal_diam')

    system_sized_df = pd.merge_asof(system_df,system_rated_df,on='internal_diam',direction='forward')

    return system_sized_df

def size_network_layer(layer,id_formula,length_formula,system_rating_bar,target_velocity,rho,mu,pres_drop_per_m):
    
    id_formula = processing.run("native:fieldcalculator", 
                                            {'INPUT':layer,
                                             'FIELD_NAME':'sizer_id_field',
                                             'FIELD_TYPE':2,
                                             'FIELD_LENGTH':0,
                                             'FIELD_PRECISION':0,
                                             'FORMULA':id_formula,
                                             'OUTPUT':'memory:'})['OUTPUT']

    length_layer = processing.run("native:fieldcalculator", 
                                            {'INPUT':id_formula,
                                             'FIELD_NAME':'sizer_length_field',
                                             'FIELD_TYPE':0,
                                             'FIELD_LENGTH':0,
                                             'FIELD_PRECISION':0,
                                             'FORMULA':length_formula,
                                             'OUTPUT':'memory:'})['OUTPUT']
    
    retained = processing.run("native:retainfields", 
                                            {'INPUT':length_layer,
                                             'FIELDS':['sizer_id_field','sizer_length_field'],
                                             'OUTPUT':'memory:'})['OUTPUT']
    
    system_df = layer_to_df(retained)
    
    sized_system_df = system_sizer(system_df,system_rating_bar,target_velocity,rho,mu,pres_drop_per_m)
    
    dataframes = [sized_system_df]
    file_names = ['system_sizing']
    
    sized_layer = dataframes_to_csv(dataframes,file_names)[0]
    
    joined_layer = processing.run("native:joinattributestable", 
                                            {'INPUT':retained,
                                             'FIELD':'sizer_id_field',
                                             'INPUT_2':sized_layer,
                                             'FIELD_2':'sizer_id_field',
                                             'FIELDS_TO_COPY':[],
                                             'METHOD':1,
                                             'DISCARD_NONMATCHING':False,
                                             'PREFIX':'','OUTPUT':'memory:'})['OUTPUT']

    return joined_layer

layer = iface.activeLayer()
id_formula = '"name"'
length_formula = '$length'
system_rating_bar = 20
target_velocity = 1.5
rho = 998
mu = 0.001
pres_drop_per_m = 400


sized = size_network_layer(layer,id_formula,length_formula,system_rating_bar,target_velocity,rho,mu,pres_drop_per_m)

QgsProject.instance().addMapLayer(sized)