import math

import pandas as pd

def beggs_brill_method(flow_rate, gas_frac,
                       liquid_density,liquid_viscosity,
                       surf_tens, pres, gas_compressibility,
                       gas_viscosity,molar_mass,fluid_temp,
                       internal_diameter,line_roughness,
                       chainage,elevation,include_acceleration_factor):

    gas_flow_rate = flow_rate * gas_frac
    liquid_flow_rate = flow_rate * (1-gas_frac)

    length = chainage

    gas_density = gas_density = ((pres*100000) * (molar_mass/1000)) / (fluid_temp * (gas_compressibility) * 8.314462618)
    
    try:
        angle = math.asin(max(min(elevation/length, 1), -1))
    except:
        angle = 0
    
    if angle < 0:
        incline = 'down'
    else:
        incline = 'up'
    
    cross_area = math.pi * ((internal_diameter/2)**2)

    # constants

    v_m = (gas_flow_rate + liquid_flow_rate) / cross_area # mixture velocity

    v_sg = gas_flow_rate / cross_area # no slip gas velocity

    v_sl = liquid_flow_rate / cross_area # no slip liquid velocity

    n_lv = 1.938 * ((v_sl*(liquid_density/(9.81*surf_tens)))**0.25) # liquid velocity number

    froude = (v_m**2) / (9.81*internal_diameter)

    c_l = liquid_flow_rate / (liquid_flow_rate + gas_flow_rate)

    l_one = 316 * (c_l**0.302)
    l_two = 0.0009252 * (c_l**(-2.4684))
    l_three = 0.1 *(c_l**(-1.4516))
    l_four = 0.5 *(c_l**(-6.738))

    beta = 0.0

    if (c_l < 0.01 and froude < l_one) or (c_l >= 0.01 and froude < l_two):
        flow_regime = 'segregated'
        a_val = 0.98
        b_val = 0.4846
        c_val = 0.0868

        if incline == 'up':
            d_val = 0.011
            e_val = -3.768
            f_val = 3.539
            g_val = -1.614

            beta = (1-c_l)*math.log(d_val*(c_l**e_val)*(n_lv**f_val)*(froude**g_val))

        liquid_holdup = (a_val * (c_l**b_val)) / (froude**c_val)

    elif (0.01 <= c_l < 0.4 and l_three < froude <= l_one) or (c_l >= 0.4 and l_three < froude <= l_four):
        flow_regime = 'intermittent'
        a_val = 0.845
        b_val = 0.5351
        c_val = 0.0173

        if incline == 'up':
            d_val = 2.96
            e_val = 0.305
            f_val = -0.4473
            g_val = 0.0978

            beta = (1-c_l)*math.log(d_val*(c_l**e_val)*(n_lv**f_val)*(froude**g_val))


        liquid_holdup = (a_val * (c_l**b_val)) / (froude**c_val)



    elif (c_l < 0.4 and froude >= l_four) or (c_l >= 0.4 and froude > l_four):
        flow_regime = 'distributed'
        a_val = 1.065
        b_val = 0.5824
        c_val = 0.0609

        if incline == 'up':
            beta = 0
            


        liquid_holdup = (a_val * (c_l**b_val)) / (froude**c_val)

    elif l_two < froude < l_three:
        cap_a_val = (l_three - froude)/(l_three-l_two)
        cap_b_val = 1 - cap_a_val

        flow_regime = 'transition'
        a_val = 0.98
        b_val = 0.4846
        c_val = 0.0868

        liquid_holdup_seg = (a_val * (c_l**b_val)) / (froude**c_val)

        a_val = 0.845
        b_val = 0.5351
        c_val = 0.0173

        liquid_holdup_int = (a_val * (c_l**b_val)) / (froude**c_val)
        
        liquid_holdup = cap_a_val * liquid_holdup_seg + cap_b_val * liquid_holdup_int
            
        liquid_holdup = liquid_holdup

    else:
        flow_regime = 'not_assigned'

    if incline == 'down':
        d_val = 2.96
        e_val = 0.305
        f_val = -0.4473
        g_val = 0.0978

        beta = (1-c_l)*math.log(d_val*(c_l**e_val)*(n_lv**f_val)*(froude**g_val))

    if liquid_holdup < c_l:
        correction = 1 + (beta*(math.sin(1.8*angle)) - ((1/3)*(math.sin(1.8*angle)** 3)))

        liquid_holdup = correction * liquid_holdup

    liquid_holdup = max(liquid_holdup, c_l)

    #if incline == 'down':
    #    liquid_holdup *= 1.15   # start with 10–20%

    mixture_density = liquid_density * liquid_holdup + gas_density*(1-liquid_holdup)

    pres_drop_elev =( mixture_density * 9.81 * math.sin(angle) * length)/100000 # bar

    # friction

    re_ns = (liquid_density * v_m * internal_diameter)/(liquid_viscosity)

    y = c_l / (liquid_holdup**2)

    if 1 < y < 1.2:
        cap_s = math.log(2.2*y-1.2)
    else:
        cap_s = math.log(y)/(-0.0523+(3.182*math.log(y))-(0.8725*(math.log(y)**2))+(0.01853*((math.log(y)**4))))

    f_ns =( 0.25 / ((math.log10((line_roughness/(3700*internal_diameter))+(5.74/(re_ns**0.9))))**2)) / 4 # no slip friction factor - fanning

    f_tp = (math.e**cap_s)*f_ns

    pres_drop_fric = ((2 * f_tp * mixture_density * v_m**2 / internal_diameter) * length)/100000

    if include_acceleration_factor:
        accel_correction_factor = ((mixture_density * 0.06242796) * (v_m* 3.281) * (v_sg* 3.281))/((9.81* 3.281)*(pres))
    else:
        accel_correction_factor = 0

    total_pres_drop = pres_drop_elev + pres_drop_fric

    #if pres_drop_elev < 0:
    #    total_pres_drop = pres_drop_fric

    total_pres_drop = (total_pres_drop/((1-accel_correction_factor)))

    inlet_pres = pres + total_pres_drop

    if inlet_pres <= 0:
        inlet_pres = pres

    bb_dict = {
        "flow_regime": flow_regime,
        "liquid_holdup": liquid_holdup,
        "re_ns": re_ns,
        "rho_m": mixture_density,
        "rho_g": gas_density,
        "v_m": v_m,
        "p_from_bar": inlet_pres,
        "p_to_bar": pres
    }

    bb_df = pd.DataFrame(bb_dict)


    return bb_df

