import math
import pandas as pd
from .friction_factor import *

def homogenous_method(flow_rate, gas_frac,
                       liquid_density,liquid_viscosity,
                       surf_tens, pres, gas_compressibility,
                       gas_viscosity,molar_mass,fluid_temp,
                       internal_diameter,line_roughness,
                       chainage,elevation,downstream):

    gas_density = ((pres*100000) * (molar_mass/1000)) / (fluid_temp * (gas_compressibility) * 8.314462618)
    
    quality_x = (gas_density * gas_frac) / (gas_density * gas_frac + liquid_density * (1 - gas_frac))
    
    rho_m = 1/((quality_x/gas_density)+((1-quality_x)/liquid_density))
    
    mu_m = (quality_x*gas_viscosity)+((1-quality_x)*(liquid_viscosity))
    
    gas_mass_flow_rate = gas_frac*flow_rate*gas_density
    liquid_mass_flow_rate = (1-gas_frac)*flow_rate*liquid_density
    
    area = math.pi*((internal_diameter/2)**2)
    
    total_mass_flux = (gas_mass_flow_rate+liquid_mass_flow_rate) / area
    
    re_d = (total_mass_flux*internal_diameter)/mu_m
    
    line_roughness_m = line_roughness / 1000
    
    friction_factor = calculate_friction_factor(re_d=re_d,line_roughness_m=line_roughness_m,internal_diameter=internal_diameter)
    
    friction_loss = ((friction_factor*(total_mass_flux**2))/(2*internal_diameter*rho_m))*chainage
    
    elevation_loss = rho_m * 9.81 * elevation
    
    total_pres_drop = (friction_loss + elevation_loss)/100000
    
    from_pres = pres + total_pres_drop
    
    if from_pres < 0:
        from_pres = pres
    
    to_pres = pres
    
    dictionary = {
        "re_d": re_d,
        "rho_m": rho_m,
        "rho_g": gas_density,
        "mol_mass_g": molar_mass,
        "z_g": gas_compressibility,
        "section_length": chainage, 
        "elev_drop": elevation_loss,
        "fric_drop": friction_loss,
        "p_from_bar": from_pres,
        "p_to_bar": to_pres
    }

    dataframe = pd.DataFrame(dictionary)

    return dataframe