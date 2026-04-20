import math
import pandas as pd
from .friction_factor import *
from scipy.optimize import fsolve

def stratified_mechanistic(flow_rate, gas_frac,
                       liquid_density,liquid_viscosity,
                       surf_tens, pres, gas_compressibility,
                       gas_viscosity,molar_mass,fluid_temp,
                       internal_diameter,line_roughness,
                       chainage,elevation,downstream):

    internal_radius = internal_diameter / 2
    
    gas_flow_rate = flow_rate * gas_frac
    liquid_flow_rate = flow_rate * (1-gas_frac)
    
    total_area = math.pi*((internal_diameter/2)**2)
    
    line_roughness_m = line_roughness/1000
    
    inclination_angle = math.atan2(elevation, chainage)
    
    gas_density = ((pres*100000) * (molar_mass/1000)) / (fluid_temp * (gas_compressibility) * 8.314462618)
    
    def residuals(vars):
        h, dPdx = vars

        # 1. geometry
    
        h = max(1e-6, min(h, 2*internal_radius - 1e-6))
    
        liquid_area = (internal_radius**2)*math.acos((internal_radius-h)/internal_radius)-(internal_radius-h)*(((2*internal_radius-(h**2))**0.5))
        
        gas_area = total_area - liquid_area
        
        theta = math.acos(max(-1, min(1, (internal_radius - h)/internal_radius)))
        
        s_l = internal_radius * theta
        s_g = (2*math.pi*internal_radius)-s_l
        s_i = 2*((2*internal_radius*h)-(h**2))
        
        gas_velocity = gas_flow_rate / gas_area
        liquid_velocity = liquid_flow_rate / liquid_area
        
        re_g = (gas_density * gas_velocity * internal_diameter) / gas_viscosity
        re_l = (liquid_density * liquid_velocity * internal_diameter) / liquid_viscosity
        
        f_g = calculate_friction_factor(re_d=re_g,
                                                        line_roughness_m=line_roughness_m,
                                                        internal_diameter=internal_diameter)
        
        f_l = calculate_friction_factor(re_d=re_l,
                                                        line_roughness_m=line_roughness_m,
                                                        internal_diameter=internal_diameter)
        
        f_i = f_g

        # 3. shear
        tau_wl = f_l*0.5*liquid_density*(liquid_velocity**2)
        tau_wg = f_g*0.5*gas_density*(gas_velocity**2)
        tau_i = f_i*0.5*liquid_density*((gas_velocity-liquid_velocity)**2)
        
        # 4. residuals
        R1 = -dPdx*liquid_area - tau_wl*s_l - tau_i*s_i - liquid_density*9.81*liquid_area*math.sin(inclination_angle)
        R2 = -dPdx*gas_area - tau_wg*s_g + tau_i*s_i - gas_density*9.81*gas_area*math.sin(inclination_angle)

        return [float(R1), float(R2)]
    
    initial_guess_h = internal_radius / 2
    initial_guess_dPdx = 1
    
    h, dPdx = fsolve(residuals, [initial_guess_h, initial_guess_dPdx])
    
    pres_loss = (dPdx*chainage)/100000
    
    from_pres = pres + (pres_loss*-1)
    
    if from_pres <0:
        from_pres = pres
        
    to_pres = pres
    
    dictionary = {
        "rho_l": liquid_density,
        "rho_g": gas_density,
        "mol_mass_g": molar_mass,
        "h": h,
        "section_length": chainage, 
        "pres_loss": pres_loss, 
        "p_from_bar": from_pres,
        "p_to_bar": to_pres
    }

    dataframe = pd.DataFrame(dictionary)

    return dataframe