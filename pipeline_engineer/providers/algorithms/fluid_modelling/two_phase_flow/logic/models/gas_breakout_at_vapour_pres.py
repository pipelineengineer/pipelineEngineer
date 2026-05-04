import math
import pandas as pd
import numpy as np
from scipy.optimize import fsolve
from .friction_factor import *

def single_phase_with_gas_breakout(flow_rate, gas_frac,
                       liquid_density,liquid_viscosity,
                       surf_tens, pres, gas_compressibility,
                       gas_viscosity,molar_mass,fluid_temp,
                       internal_diameter,line_roughness,
                       chainage,elevation,downstream):

    gas_density = ((pres*100000) * (molar_mass/1000)) / (fluid_temp * (gas_compressibility) * 8.314462618)
    
    area = math.pi*((internal_diameter/2)**2)
    
    velocity = flow_rate / area
    
    re_d = (liquid_density*internal_diameter*velocity)/liquid_viscosity
    
    line_roughness_m = line_roughness / 1000
    
    friction_factor = calculate_friction_factor(re_d=re_d,line_roughness_m=line_roughness_m,internal_diameter=internal_diameter)
    
    friction_loss = ((friction_factor*(velocity**2)*liquid_density)/(2*internal_diameter))*chainage
    
    elevation_loss = liquid_density * 9.81 * elevation
    
    total_pres_drop = (friction_loss + elevation_loss)/100000
    
    from_pres = pres + total_pres_drop
    
    vapour_pres = (10**(8.07131-(1730.63/(233.426+(fluid_temp - 273.15))))) * 0.0013333
    
    if from_pres <= vapour_pres: # Slack Flow Trigger - Assuming gas breakout occurs when this condition is met
 
        re_g = (velocity * gas_density * internal_diameter)/gas_viscosity
 
        friction_factor_gas = calculate_friction_factor(re_d=re_g,line_roughness_m=line_roughness_m,internal_diameter=internal_diameter)
    
        friction_loss_gas = ((friction_factor_gas*(velocity**2)*gas_density)/(2*internal_diameter))*chainage
        
        elevation_loss_gas = gas_density * 9.81 * elevation
        
        from_pres = vapour_pres + ((elevation_loss_gas + friction_loss_gas)/100000)
 
    to_pres = pres
    
    dictionary = {
        "re_d": [re_d],
        "rho": [liquid_density],
        "section_length": [chainage], 
        "elev_drop": [elevation_loss],
        "fric_drop": [friction_loss],
        "p_from_bar": [from_pres],
        "p_to_bar": [to_pres]
    }

    dataframe = pd.DataFrame(dictionary)

    return dataframe