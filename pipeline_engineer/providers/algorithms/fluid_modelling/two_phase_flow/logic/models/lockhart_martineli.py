import math
import pandas as pd
from .friction_factor import *

def lockhart_martinelli(flow_rate, gas_frac,
                       liquid_density,liquid_viscosity,
                       surf_tens, pres, gas_compressibility,
                       gas_viscosity,molar_mass,fluid_temp,
                       internal_diameter,line_roughness,
                       chainage,elevation,downstream):

    gas_density = ((pres*100000) * (molar_mass/1000)) / (fluid_temp * (gas_compressibility) * 8.314462618)
    
    quality_x = (gas_density * gas_frac) / (gas_density * gas_frac + liquid_density * (1 - gas_frac))
    
    gas_mass_flow_rate = gas_frac*flow_rate*gas_density
    liquid_mass_flow_rate = (1-gas_frac)*flow_rate*liquid_density
    
    area = math.pi*((internal_diameter/2)**2)
    
    j_g = gas_frac * flow_rate / area
    j_l = (1 - gas_frac) * flow_rate / area
    
    re_g = (gas_density * j_g * internal_diameter) / gas_viscosity
    re_l = (liquid_density * j_l * internal_diameter) / liquid_viscosity
    
    line_roughness_m = line_roughness/1000
    
    f_g = calculate_friction_factor(re_d=re_g,
                                                    line_roughness_m=line_roughness_m,
                                                    internal_diameter=internal_diameter)
    
    f_l = calculate_friction_factor(re_d=re_l,
                                                    line_roughness_m=line_roughness_m,
                                                    internal_diameter=internal_diameter)
    
    dpdz_g = (f_g * gas_density * j_g**2) / (2 * internal_diameter)
    dpdz_l = (f_l * liquid_density * j_l**2) / (2 * internal_diameter)
    
    
    if dpdz_g == 0:
        X = 1e6
    else:
        X = (dpdz_l / dpdz_g)**0.5
    
    if re_l < 2000 and re_g < 2000:
        C = 5      # laminar–laminar
    elif re_l < 2000 and re_g >= 2000:
        C = 10     # laminar–turbulent
    elif re_l >= 2000 and re_g < 2000:
        C = 12     # turbulent–laminar
    else:
        C = 20     # turbulent–turbulent
    
    phi_l_sq = 1 + C/X + 1/X**2

    dpdz_tp = phi_l_sq * dpdz_l
    friction_loss = dpdz_tp * chainage
    
    rho_m = 1/((quality_x/gas_density)+((1-quality_x)/liquid_density))
    
    elevation_loss = rho_m * 9.81 * elevation
    
    total_pres_drop = (friction_loss + elevation_loss)/100000
    
    from_pres = pres + total_pres_drop
    
    if from_pres < 0:
        from_pres = pres
    
    to_pres = pres
    
    dictionary = {
        "re_g": re_g,
        "re_l": re_l,
        "rho_m": rho_m,
        "rho_g": gas_density,
        "mol_mass_g": molar_mass,
        "z_g": gas_compressibility,
        "phi_l_sq": phi_l_sq,
        "section_length": chainage, 
        "elev_drop": elevation_loss,
        "fric_drop": friction_loss,
        "p_from_bar": from_pres,
        "p_to_bar": to_pres
    }

    dataframe = pd.DataFrame(dictionary)

    return dataframe