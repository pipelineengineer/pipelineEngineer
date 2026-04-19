import math
from scipy.optimize import fsolve

def calculate_friction_factor(re_d,line_roughness_m,internal_diameter):
    
    if re_d < 2100:
        
        friction_factor = 64/re_d
        
    else:
        
        def colebrook_friction_factor(friction_factor):
            
            rhs = 1 / (friction_factor**0.5)
            
            lhs = -2*math.log10((line_roughness_m/(3.7*internal_diameter))+(2.51/((re_d*(friction_factor**0.5)))))
            
            return rhs-lhs
        
        friction_factor = fsolve(colebrook_friction_factor, x0=0.01)[0]
    
    return friction_factor