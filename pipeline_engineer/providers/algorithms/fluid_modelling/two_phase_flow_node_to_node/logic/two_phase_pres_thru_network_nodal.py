import pandas as pd
import math
import numpy as np
from ...general_logic.function_helpers import *
from ...two_phase_correlations.homogeneous import *
from ...two_phase_correlations.lockhart_martinelli import *
from ...two_phase_correlations.beggs_brill import *

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

def estimate_free_gas_mass_flow(temp_k,k_h,gas_molar_mass,water_mass,gas_mass,water_density,pres,correct_salinity,salt_ppm,c_salt,salt_mol_mass):

    pres_bara = (pres+1.013)

    gas_density = ((pres_bara*100000) * (gas_molar_mass/1000)) / (temp_k*8.314)
    
    if correct_salinity:
        sal_g_per_kg = salt_ppm / 1000
        sal_mol_per_kg = sal_g_per_kg / salt_mol_mass

        salt_correction = 1/(10**(c_salt*sal_mol_per_kg))
    else:
        salt_correction = 1

    gas_mass_kg_per_kg_water = (pres_bara * k_h * gas_molar_mass * salt_correction)/1000
    
    gas_mass_kg = min(water_mass * gas_mass_kg_per_kg_water, gas_mass)
    free_gas = gas_mass - gas_mass_kg
    
    return free_gas

def two_phase_pres_through_network_nodal(network_df,boundaries_df,junction_heights_df,
                                   liquid_density,liquid_viscosity,
                                   gas_molar_mass,gas_viscosity,fluid_temp,
                                   k_h,salt_ppm,c_salt,salt_mol_mass,
                                   surf_tens,apply_henrys_law,correct_salinity,correlation):
    i = 0
    
    if 'in_service' in boundaries_df.columns.tolist(): 
    
        boundaries_df = boundaries_df[boundaries_df['in_service'] != False]
        
    known_junctions_df = boundaries_df[['junction','p_bar']]
    to_junctions = network_df['to_junction'].tolist()
    from_junctions = network_df['from_junction'].tolist()
    junctions = set(to_junctions + from_junctions)
    known_junctions = known_junctions_df['junction'].tolist()
    unknown_junctions = [item for item in junctions if item not in known_junctions]

    lst = network_df['l_mdot_kg_per_s'].tolist()
    count = sum(1 for x in lst if x != 0)

    pump_to_junctions = []
    pump_from_junctions = []
    
    total_lines = []
    processed_lines = set()
    network_mesh_df = pd.DataFrame()

    used_pumps = set()

    while len(unknown_junctions) > 0 and i < len(known_junctions_df):

        junction = known_junctions_df['junction'].iloc[i]
        pres = known_junctions_df['p_bar'].iloc[i]

        if junction in pump_to_junctions and two_phase_layers:
            
            connected_pumps_df = pump_df[(pump_df['to_junction'] == junction) &(~pump_df['name'].isin(used_pumps))]
            
            for _,row in connected_pumps_df.iterrows():
                
                pump_curve = row['std_type']
                pump_from_junction = row['from_junction']
                pump_name = row['name']
            
                lines_connected_df = network_df[network_df['to_junction'] == pump_from_junction]
                vol_flow_m_cubed_per_h = (sum(lines_connected_df['l_mdot_kg_per_s'].tolist()) / (liquid_density))*60*60
                
                if pump_curve == 'P3':
                    from_jct_pres = pres - (-0.00001*vol_flow_m_cubed_per_h+5)
                    
                elif pump_curve == 'P2':
                    from_jct_pres = pres - (-3.125e-4*(vol_flow_m_cubed_per_h**2) - 1.25e-2*(vol_flow_m_cubed_per_h) + 10)
                    
                elif pump_curve == 'P1':
                    from_jct_pres = pres - (-2.08e-4*(vol_flow_m_cubed_per_h**2) - 3.33e-3*(vol_flow_m_cubed_per_h) + 6.1)

                found_pressures_df = pd.DataFrame({"junction": [pump_from_junction], "p_bar": [from_jct_pres]})
                
                known_junctions_df = pd.concat(
                    [known_junctions_df, found_pressures_df],
                    ignore_index=True
                )
                
                used_pumps.add(pump_name)
                
        elif junction in pump_from_junctions:
            
            connected_pumps_df = pump_df[(pump_df['from_junction'] == junction)&(~pump_df['name'].isin(used_pumps))]
            
            for _,row in connected_pumps_df.iterrows():
                
                pump_curve = row['std_type']
                pump_to_junction = row['to_junction']
                pump_name = row['name']
            
                lines_connected_df = network_df[network_df['to_junction'] == pump_to_junction]
                vol_flow_m_cubed_per_h = (sum(lines_connected_df['l_mdot_kg_per_s'].tolist()) / (liquid_density))*60*60
                
                if pump_curve == 'P3':
                    from_jct_pres = pres + (-0.00001*vol_flow_m_cubed_per_h+5)
                    
                elif pump_curve == 'P2':
                    from_jct_pres = pres + (-3.125e-4*(vol_flow_m_cubed_per_h**2) - 1.25e-2*(vol_flow_m_cubed_per_h) + 10)
                    
                elif pump_curve == 'P1':
                    from_jct_pres = pres + (-2.08e-4*(vol_flow_m_cubed_per_h**2) - 3.33e-3*(vol_flow_m_cubed_per_h) + 6.1)

                found_pressures_df = pd.DataFrame({"junction": [pump_to_junction], "p_bar": [from_jct_pres]})
                
                known_junctions_df = pd.concat(
                    [known_junctions_df, found_pressures_df],
                    ignore_index=True
                )
                
                used_pumps.add(pump_name)
                
        connected_lines_df = network_df[(network_df['from_junction'] == junction) | (network_df['to_junction'] == junction) ]

        for _, row in connected_lines_df.iterrows():
            line_name = row['name']

            if line_name in processed_lines:
                continue

            processed_lines.add(line_name)

            from_junction = row['from_junction']
            to_junction = row['to_junction']
            internal_diameter = row['diameter_m']
            roughness = row['k_mm']/1000
            length = row['length_km']*1000
            liquid_mass_rate = row['l_mdot_kg_per_s']
            gas_mass_rate = row['g_mdot_kg_per_s']

            try:
                from_height = junction_heights_df.loc[df["name"] == from_junction, "height_m"].iloc[0]
                to_height = junction_heights_df.loc[df["name"] == to_junction, "height_m"].iloc[0]
                elevation = from_height - to_height
            except:
                elevation = 0

            if junction == from_junction:
                known = 'from_pres'
            else:
                known = 'to_pres'

            if junction == from_junction:
                if to_junction in known_junctions:
                    continue

            else: 
                if from_junction in known_junctions:
                    continue
            
            gas_density = (((pres +1.013)*100000)*(gas_molar_mass/1000))/(fluid_temp*8.314)
            
            if apply_henrys_law:

                gas_mass_rate = estimate_free_gas_mass_flow(temp_k=fluid_temp,
                                                     k_h=k_h,
                                                     gas_molar_mass=gas_molar_mass,
                                                     water_mass=liquid_mass_rate,
                                                     gas_mass=gas_mass_rate,
                                                     water_density=liquid_density,
                                                     pres=pres,correct_salinity=correct_salinity,
                                                     salt_ppm=salt_ppm,
                                                     c_salt=c_salt,
                                                     salt_mol_mass=salt_mol_mass)
            
            if correlation == 'homogeneous':
                pres_drop_dict = homogeneous_pres_drop(d=internal_diameter,roughness=roughness,
                                                       length=length,elev=elevation,
                                                       mdot_l=liquid_mass_rate,mdot_g=gas_mass_rate,
                                                       rho_l=liquid_density,rho_g=gas_density,
                                                       mu_l=liquid_viscosity,mu_g=gas_viscosity)
            
            elif correlation == 'lockhart_martinelli':
                pres_drop_dict = lockhart_martinelli_pres_drop(d=internal_diameter,roughness=roughness,
                                                               length=length,elev=elevation,
                                                               mdot_l=liquid_mass_rate,mdot_g=gas_mass_rate,
                                                               rho_l=liquid_density,rho_g=gas_density,
                                                               mu_l=liquid_viscosity,mu_g=gas_viscosity)

            elif correlation == 'beggs_brill':
                pres_drop_dict = beggs_brill_pres_drop(d=internal_diameter,roughness=roughness,
                                                               length=length,elev=elevation,
                                                               mdot_l=liquid_mass_rate,mdot_g=gas_mass_rate,
                                                               rho_l=liquid_density,rho_g=gas_density,
                                                               mu_l=liquid_viscosity,mu_g=gas_viscosity,sigma=surf_tens)

            if known == 'from_pres':
                inlet_pres = pres
                try:
                    outlet_pres = pres - pres_drop_dict['total_loss_bar'][0]
                except:
                    outlet_pres = pres - pres_drop_dict['total_loss_bar']
                df_entry = pd.DataFrame([{"junction":to_junction,"p_bar":outlet_pres}])
                known_junctions_df = pd.concat([known_junctions_df,df_entry],ignore_index=True)
                
            else:
                try:
                    inlet_pres = pres + pres_drop_dict['total_loss_bar'][0]
                except:
                    inlet_pres = pres + pres_drop_dict['total_loss_bar']
                outlet_pres = pres
                
                df_entry = pd.DataFrame([{"junction":from_junction,"p_bar":inlet_pres}])
                known_junctions_df = pd.concat([known_junctions_df,df_entry],ignore_index=True)

            line_results = {
                "line_name": row['name'],
                "p_from_bar": inlet_pres,
                "p_to_bar": outlet_pres
            }

            line_results = line_results | pres_drop_dict

            total_lines.append(line_results)

            known_junctions = known_junctions_df['junction'].tolist()

            unknown_junctions = [item for item in junctions if item not in known_junctions]
            
            #break
        i = i+1
        #break

    results_df = pd.DataFrame(total_lines)

    line_pressures_df = pd.merge(left=network_df,right=results_df,how='left',left_on='name',right_on='line_name')
    line_pressures_df = line_pressures_df.dropna(subset=['p_from_bar'])
    line_pressures_df =  line_pressures_df.drop(columns=['line_name'])

    return known_junctions_df, line_pressures_df