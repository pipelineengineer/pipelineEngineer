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

def lockhart_martinelli_pres_drop(d,roughness,length,elev,mdot_l,mdot_g,rho_l,rho_g,mu_l,mu_g):
    
    area = math.pi * ((d/2)**2)
    
    q_l = mdot_l / rho_l #m^3/s
    q_g = mdot_g / rho_g #m^3/s

    v_l = q_l / area
    v_g = q_g / area
    
    re_l = (rho_l*v_l*d)/mu_l
    re_g = (rho_g*v_g*d)/mu_g

    f_l = calculate_friction_factor(re_d=re_l,line_roughness_m=roughness,internal_diameter=d)
    f_g = calculate_friction_factor(re_d=re_g,line_roughness_m=roughness,internal_diameter=d)

    q_m = q_l + q_g

    gvf = q_g / q_m

    rho_m = (1-gvf)*rho_l + rho_g*gvf

    # Pres Drop
    dp_per_m_fric_l = (f_l*rho_l*v_l**2)/(2*d)
    dp_per_m_fric_g = (f_g*rho_g*v_g**2)/(2*d)
    
    x = (dp_per_m_fric_l/dp_per_m_fric_g)**0.5

    if re_l < 2100 and re_g < 2100:
        c = 5
    elif re_l > 2100 and re_g < 2100:
        c = 10
    elif re_l < 2100 and re_g > 2100:
        c = 12
    else:
        c = 20

    tp_multiplier = 1+(c/x)+(1/(x**2))

    dp_static = (rho_m*9.81*elev)/100000
   
    dp_fric = (dp_per_m_fric_l * tp_multiplier * length) /100000

    dp_total = (dp_fric + dp_static)
    
    if pd.isna(dp_total):
        dp_total = 0

    bb_results = {
        "area": area,
        "q_l": q_l,
        "q_g": q_g,
        "q_m": q_m,
        "v_l": v_l,
        "v_g": v_g,
        "gvf": gvf,
        "rho_m": rho_m,
        "re_l": re_l,
        "re_g": re_g,
        "f_l": f_l,
        "f_g": f_g,
        "dp_per_m_fric_l": dp_per_m_fric_l,
        "dp_per_m_fric_g": dp_per_m_fric_g,
        "x": x,
        "c": c,
        "dp_fric": dp_fric,
        "dp_static": dp_static,
        "total_loss_bar": dp_total
    }

    return bb_results