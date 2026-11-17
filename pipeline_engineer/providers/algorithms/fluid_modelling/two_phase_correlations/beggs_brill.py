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
        
    friction_factor = friction_factor/4
    
    return friction_factor

def apply_liquid_holdup_correction(regime,c_l,n_fr):

    liquid_holdup_coefficents = {'segregated': (0.980, 0.4846,0.0868),
                                 'intermittent': (0.845, 0.5351,0.0173),
                                 'distributed': (1.065,0.5824,0.0609)}

    a,b,c = liquid_holdup_coefficents[regime]

    return max((a*((c_l)**b)) / (n_fr**c),c_l)

def find_upper_c(regime,c_l,upward_incline,n_lv,n_fr):

    if regime == 'distributed':
        upper_c = 0
        return upper_c
    
    if upward_incline:

        upper_c_coefficents = {'segregated': (0.011, -3.7680, 3.5390, -1.6140),
                               'intermittent': (2.960, 0.3050,-0.4473, 0.0978)}
    

        e,f,g,h = upper_c_coefficents[regime]

    else:
        e = 4.700
        f = -0.3692
        g = 0.1244
        h = -0.5056

    upper_c =  max((1-c_l)*math.log(e*(c_l**f)*(n_lv**g)*(n_fr**h)),0)

    return upper_c

def beggs_brill_pres_drop(d,roughness,length,elev,mdot_l,mdot_g,
                          rho_l,rho_g,mu_l,mu_g,sigma):
    
    if d <= 0:
        raise ValueError("Diameter must be greater than zero.")

    #if length <= 0:
    #    raise ValueError("Length must be greater than zero.")
    
    #if abs(elev) > length:
    #    raise ValueError("Absolute elevation cannot exceed pipe length.")
    
    #if rho_l <= 0 or rho_g <= 0:
    #    raise ValueError("Densities must be greater than zero.")

    #if mu_l <= 0 or mu_g <= 0:
    #    raise ValueError("Viscosities must be greater than zero.")

    #if sigma <= 0:
    #    raise ValueError("Surface tension must be greater than zero.")
    
    area = math.pi * ((d/2)**2)
    angle = math.asin(elev/length)
    upward_incline = (elev > 0)
    
    q_l = mdot_l / rho_l #m^3/s
    q_g = mdot_g / rho_g #m^3/s

    v_sl = q_l / area #m/s
    v_sg = q_g / area #m/s

    q_m = q_l + q_g #m^3/s

    if q_m <= 0:
        
        bb_results = {
        
            "area": area,
            "angle": angle,
            "upward_incline": upward_incline,

            "q_l": 0,
            "q_g": 0,
            "v_sl": 0,
            "v_sg": 0,
            "q_m": 0,

            "c_l": 0,
            
            "regime": 'no flow',

            "n_re": 0,
            "f_n": 0,

            "dp_per_m_fric": 0,
            "dp_static": 0,

            "dp_fric": 0,
            "total_loss_bar": 0
        }
        return bb_results

    v_m = q_m / area #m/s

    n_fr = (v_m**2)/(9.81*d)
    c_l = q_l / q_m

    rho_n = c_l*rho_l + (rho_g*(1-c_l))
    mu_n = mu_l*c_l+mu_g*(1-c_l)

    n_lv = (v_sl *(rho_l / (9.81 * sigma))**0.25)
    
    # flow pattern transition boundaries
    #l_one = 316*(c_l**0.302)
    #l_two = 0.000925*(c_l**(-2.468))
    #l_three = 0.1*(c_l**(-1.452))
    #l_four = 0.5*(c_l**(-6.738))

    l_one = 316.0 * c_l**0.302
    l_two = 0.0009252 * c_l**(-2.4684)
    l_three = 0.10 * c_l**(-1.4516)
    l_four = 0.50 * c_l**(-6.738)

    # regime classification
    if c_l <= 0:
        re = (v_sg*rho_g*d)/mu_g
        
        f_n = calculate_friction_factor(re_d=re,line_roughness_m=roughness,internal_diameter=d)*4
        
        dp_per_m_fric = (f_n*rho_g*v_sg**2)/(2*d)

        dp_static = (rho_g*9.81*elev)/100000
       
        dp_fric = (dp_per_m_fric * length) /100000
        
        total_loss = dp_static + dp_fric
        
        bb_results = {
        
            "area": area,
            "angle": angle,
            "upward_incline": upward_incline,

            "q_l": 0,
            "q_g": q_g,
            "v_sl": 0,
            "v_sg": v_sg,
            "q_m": q_g,

            "c_l": 0,
            
            "regime": 'gaseous',

            "n_re": re,
            "f_n": f_n,

            "dp_per_m_fric": dp_per_m_fric,
            "dp_static": dp_static,

            "dp_fric": dp_fric,
            "total_loss_bar": total_loss
        }
        return bb_results
        
    elif c_l >= 1:
        re = (v_sl*rho_l*d)/mu_l
        
        f_n = calculate_friction_factor(re_d=re,line_roughness_m=roughness,internal_diameter=d)*4
        
        dp_per_m_fric = (f_n*rho_l*v_sl**2)/(2*d)

        dp_static = (rho_l*9.81*elev)/100000
       
        dp_fric = (dp_per_m_fric * length) /100000
        
        total_loss = dp_static + dp_fric
        
        bb_results = {
        
            "area": area,
            "angle": angle,
            "upward_incline": upward_incline,

            "q_l": q_l,
            "q_g": 0.0,
            "v_sl": v_sl,
            "q_m": q_l,

            "c_l": 1,
            
            "regime": 'liquid',

            "n_re": re,
            "f_n": f_n,

            "dp_per_m_fric": dp_per_m_fric,
            "dp_static": dp_static,

            "dp_fric": dp_fric,
            "total_loss_bar": total_loss
        }
        return bb_results
    
    else:
        if (c_l < 0.01 and n_fr < l_one) or (c_l >= 0.01 and n_fr < l_two):
            regime = 'segregated'
        elif c_l >= 0.01 and l_two <= n_fr <= l_three:
            regime = 'transition'
        elif (0.01 <= c_l and c_l < 0.4 and l_three < n_fr <= l_one) or (c_l >= 0.4 and l_three < n_fr <= l_four):
            regime = 'intermittent'
        elif (c_l < 0.4 and n_fr >= l_one) or (c_l >= 0.4 and n_fr > l_four):
            regime = 'distributed'
        else:
            regime = 'segregated'

    if regime == 'transition':

        h_l_seg = apply_liquid_holdup_correction(regime='segregated',c_l=c_l,n_fr=n_fr)
        upper_c_seg = find_upper_c(regime='segregated',c_l=c_l,
                                   upward_incline=upward_incline,
                                   n_lv=n_lv,n_fr=n_fr)
        phi_seg = 1 + upper_c_seg * (math.sin(1.8*angle)-(0.333*((math.sin(1.8*angle))**3)))
        h_l_seg = h_l_seg * phi_seg

        h_l_int = apply_liquid_holdup_correction(regime='intermittent',c_l=c_l,n_fr=n_fr)
        upper_c_int = find_upper_c(regime='intermittent',c_l=c_l,
                                    upward_incline=upward_incline,
                                    n_lv=n_lv,n_fr=n_fr)
        phi_int = 1 + upper_c_int * (math.sin(1.8*angle)-(0.333*((math.sin(1.8*angle))**3)))
        h_l_int = h_l_int * phi_int

        upper_a = (l_three-n_fr)/(l_three-l_two)

        h_l = upper_a * h_l_seg + ((1-upper_a)*h_l_int)

    else:
        h_l = apply_liquid_holdup_correction(regime=regime,c_l=c_l,n_fr=n_fr)
        upper_c = find_upper_c(regime=regime,c_l=c_l,
                                upward_incline=upward_incline,
                                n_lv=n_lv,n_fr=n_fr)
        phi = 1 + upper_c * (math.sin(1.8*angle)-(0.333*((math.sin(1.8*angle))**3)))
        h_l = h_l * phi

    h_l = min(max(h_l,c_l),1.0)

    #if angle > 0:
    #    h_l = 0.924*h_l

    #if angle < 0:
    #    h_l = 0.685*h_l

    n_re = (rho_n*v_m*d)/mu_n

    f_n = calculate_friction_factor(re_d=n_re,line_roughness_m=roughness,internal_diameter=d)

    y = c_l / (h_l**2)

    ln_y = math.log(y)

    if y <= 1.0:
        s = 0.0
    elif y < 1.2:
        s = math.log(2.2 * y - 1.2)
    else:
        s = ln_y / (
            -0.0523
            + 3.182 * ln_y
            - 0.8725 * ln_y**2
            + 0.01853 * ln_y**4
        )
        
    f = (math.e**s) * f_n

    # Pres Drop
    rho_s = h_l*rho_l + (1-h_l)*rho_g 

    dp_per_m_fric = (f*rho_n*(v_m**2))/(d)

    dp_static = (rho_s*9.81*elev)/100000
   
    dp_fric = (dp_per_m_fric * length) /100000

    total_loss_bar = (dp_fric + dp_static)
    
    if pd.isna(total_loss_bar):
        total_loss_bar = 0

    bb_results = {
        "area": area,
        "angle": angle,
        "upward_incline": upward_incline,

        "q_l": q_l,
        "q_g": q_g,
        "v_sl": v_sl,
        "q_m": q_m,
        "v_m": v_m,

        "n_fr": n_fr,
        "c_l": c_l,

        "rho_n": rho_n,
        "mu_n": mu_n,

        "n_lv": n_lv,

        "l_one": l_one,
        "l_two": l_two,
        "l_three": l_three,
        "l_four": l_four,

        "regime": regime,

        "h_l": h_l,

        "n_re": n_re,
        "f_n": f_n,

        "y": y,
        "s": s,
        "f": f,

        "rho_s": rho_s,

        "dp_per_m_fric": dp_per_m_fric,
        "dp_static": dp_static,

        "dp_fric": dp_fric,
        "total_loss_bar": total_loss_bar
    }

    return bb_results