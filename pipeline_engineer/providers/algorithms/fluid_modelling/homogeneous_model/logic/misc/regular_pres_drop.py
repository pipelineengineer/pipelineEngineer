import math

import pandas as pd

def regular_pressure_drop(
        flow_rate, density, viscosity,
        pres, internal_diameter, line_roughness,
        length, elevation
        ):
    
    # Pipe
    internal_area = math.pi * ((internal_diameter / 2)**2)
    velocity = flow_rate / internal_area

    #Frictional Loss
    
    re_d = (internal_diameter * density * velocity) / viscosity

    if re_d < 2000:
        friction_factor = 64/re_d
    else:
        friction_factor = ( 0.25 / ((math.log10((line_roughness/(3700*internal_diameter))+(5.74/(re_d**0.9))))**2))
    
    friction_loss = (friction_factor * density * length * (velocity**2))/(2*internal_diameter)

    elev_loss = elevation * 9.81 * density

    total_drop = (friction_loss + elev_loss)/100000

    inlet_pres = pres + total_drop

    dict = {
        "re_d": [re_d],
        "internal_area": [internal_area],
        "velocity": [velocity],
        "p_from_bar": [inlet_pres],
        "p_to_bar": [pres]
    }

    df = pd.DataFrame(dict)

    return df

