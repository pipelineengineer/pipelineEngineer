import os

import math
import pandas as pd
import numpy as np
from scipy.optimize import fsolve
from .friction_factor import *

def find_hydraulic_height(height,diameter,elevation,length):

    radius = diameter / 2

    area = ((radius**2)*np.arccos((radius-height)/radius)) - ((radius-height)*(np.sqrt((2*radius*height)-(height**2))))

    theta = 2*(np.arccos((radius-height)/radius))

    wetted_perimeter = theta*radius

    if length == 0:
        
        slope = 1
    
    else:
        slope = abs(elevation) / length

    calc_flow_rate = (1/roughness)*(area)*((area/wetted_perimeter)**(2/3))*((np.sqrt(slope)))

    return calc_flow_rate - flow_rate

def single_phase(flow_rate, gas_frac,
                       liquid_density,liquid_viscosity,
                       surf_tens, pres, gas_compressibility,
                       gas_viscosity,molar_mass,fluid_temp,
                       internal_diameter,line_roughness,
                       chainage,elevation,downstream):

    #script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))))
    #user_fluids_path = os.path.join(script_dir, 'user_settings','user_fluids.csv')

    #print(user_fluids_path)

    #user_fluids_df = pd.read_csv(user_fluids_path)
    
    #default_gases = ["hgas","lgas","hydrogen","methane","biomethane_pure","biomethane_treated","air"]
    
    #user_gases_df = user_fluids_df[user_fluids_df['is_gas'] == True]
    #user_gases_list = user_gases_df['name'].tolist()
    
    #if fluid in default_gases or fluid in user_gases_list:
    #    is_gas = True
    #    gas_density = ((pres*100000) * (molar_mass/1000)) / (fluid_temp * (gas_compressibility) * 8.314462618)
    #    viscosity = gas_viscosity
        
    #else:
    #    is_gas = False
    #    density = liquid_density
    #    viscosity = liquid_viscosity
    
    density = liquid_density
    viscosity = liquid_viscosity
    
    area = math.pi*((internal_diameter/2)**2)
    
    velocity = flow_rate / area
    
    re_d = (density*internal_diameter*velocity)/liquid_viscosity
    
    line_roughness_m = line_roughness / 1000
    
    friction_factor = calculate_friction_factor(re_d=re_d,line_roughness_m=line_roughness_m,internal_diameter=internal_diameter)
    
    friction_loss = ((friction_factor*(velocity**2)*density)/(2*internal_diameter))*chainage
    
    elevation_loss = density * 9.81 * elevation
    
    total_pres_drop = (friction_loss + elevation_loss)/100000
    
    from_pres = pres + total_pres_drop
 
    to_pres = pres
    
    dictionary = {
        "re_d": [re_d],
        "rho": [density],
        "section_length": [chainage], 
        "elev_drop": [elevation_loss],
        "fric_drop": [friction_loss],
        "p_from_bar": [from_pres],
        "p_to_bar": [to_pres]
    }

    dataframe = pd.DataFrame(dictionary)

    return dataframe