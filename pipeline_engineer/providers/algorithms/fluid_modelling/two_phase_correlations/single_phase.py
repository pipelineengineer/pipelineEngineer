import math
import pandas as pd

def calculate_friction_factor(re_d,line_roughness_m,internal_diameter):
    if re_d < 2100:
        friction_factor = 64/re_d  
    else:
        friction_factor = 0.25 / (
            math.log10(
                (line_roughness_m / (3.7 * internal_diameter)) +
                (5.74 / (re_d ** 0.9))
            ) ** 2
        )
    return friction_factor

def single_phase_pres_drop(d,roughness,length,elev,mdot_l,rho_l,mu_l):
    
    area = math.pi * ((d/2)**2)
    
    q_l = mdot_l / rho_l #m^3/s

    v_l = q_l / area #m/s
    
    n_re = (rho_l*v_l*d)/mu_l

    f_n = calculate_friction_factor(re_d=n_re,line_roughness_m=roughness,internal_diameter=d)

    # Pres Drop
    dp_per_m_fric = (f_n*rho_l*v_l**2)/(2*d)

    dp_static = (rho_l*9.81*elev)/100000
   
    dp_fric = (dp_per_m_fric * length) /100000

    dp_total = (dp_fric + dp_static)
    
    if pd.isna(dp_total):
        dp_total = 0

    bb_results = {
        "area": area,
        "q_l": q_l,
        "rho_l": rho_l,
        "mu_l": mu_l,
        "v_l": v_l,
        "n_re": n_re,
        "f_n": f_n,
        "dp_per_m_fric": dp_per_m_fric,
        "dp_fric": dp_fric,
        "dp_static": dp_static,
        "total_loss_bar": dp_total
    }

    return bb_results