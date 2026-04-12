import math

import pandas as pd

import pandapipes as pp

def homogenous_method(flow_rate, gas_frac,
                       liquid_density,liquid_viscosity,
                       surf_tens, pres, gas_compressibility,molar_mass,fluid_temp,
                       internal_diameter,line_roughness,
                       chainage,elevation,downstream):

    gas_density = ((pres*100000) * (molar_mass/1000)) / (fluid_temp * (gas_compressibility) * 8.314462618)
    
    quality_x = (flow_rate*gas_frac*gas_density) / (((1-gas_frac)*flow_rate*liquid_density)+(flow_rate*gas_frac*gas_density))

    phi = 1 + (quality_x*((liquid_density/gas_density)-1))

    try:
        angle = math.asin(max(min(elevation/chainage, 1), -1))
    except:
        angle = 0
    
    #print(angle)
    
    length = math.cos(angle) * chainage
    
    if angle < 0:
        incline = 'down'
    else:
        incline = 'up'
    
    cross_area = math.pi * ((internal_diameter/2)**2)

    v_m = flow_rate / cross_area

    mixture_density = liquid_density * (1-gas_frac) + gas_density * gas_frac

    pres_drop_elev =( mixture_density * 9.81 * elevation)/100000 # bar

    # friction

    re = (mixture_density * v_m * internal_diameter)/(liquid_viscosity)

    if re < 2000:
        f_f = 64/re
        
    else:
        f_f =( 0.25 / ((math.log10((line_roughness/(3700*internal_diameter))+(5.74/(re**0.9))))**2))

    pres_drop_fric = ((2 * f_f * mixture_density * v_m**2 / internal_diameter) * length * phi)/100000

    total_pres_drop = pres_drop_elev + pres_drop_fric

    inlet_pres = pres + total_pres_drop 

    if inlet_pres <= 0:
        inlet_pres = pres

    if downstream:
        from_pres = pres
        if pres - total_pres_drop < 0:
            
            to_pres = pres
        
        else:
            
            to_pres = pres - total_pres_drop
        
    else:
        to_pres = pres
        
        
        if pres + total_pres_drop < 0:
            
            from_pres = pres
            
        else:
            
            from_pres = pres + total_pres_drop
        
    dictionary = {
        "re_d": re,
        "rho_m": mixture_density,
        "rho_g": gas_density,
        "mol_mass_g": molar_mass,
        "z_g": gas_compressibility,
        "phi": phi,
        "v_m": v_m,
        "section_length": length, 
        "elev_drop": pres_drop_elev,
        "fric_drop": pres_drop_fric,
        "p_from_bar": from_pres,
        "p_to_bar": to_pres
    }

    dataframe = pd.DataFrame(dictionary)


    return dataframe

