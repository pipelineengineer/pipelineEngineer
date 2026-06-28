import pandas as pd
import math
import numpy as np
from ...general_logic.function_helpers import *

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

def create_line_mesh(line_xyz_df,known,pres,mass_flow_rate,internal_diameter,roughness,multiplier,liquid_density,liquid_viscosity,vapour_pres,fluid_temp):

    vol_flow_rate = mass_flow_rate / liquid_density

    liquid_flow_rate = vol_flow_rate

    area = math.pi*((internal_diameter/2)**2)
    velocity = vol_flow_rate / area
    re_d = (velocity * liquid_density * internal_diameter) / (liquid_viscosity)
    friction_factor = calculate_friction_factor(re_d=re_d,line_roughness_m=roughness,internal_diameter=internal_diameter)

    line_mesh_df = line_xyz_df.copy()
    line_mesh_df = line_mesh_df.sort_values('chainage_m')
    line_mesh_df['section_id'] = (line_mesh_df['name'].astype(str)+ '_'+ line_mesh_df['chainage_m'].astype(str)+ '_'+ line_mesh_df['chainage_m'].shift(-1).astype(str))
    line_mesh_df['end_xcoord'] = (line_mesh_df['xcoord'].shift(-1))
    line_mesh_df['end_ycoord'] = (line_mesh_df['ycoord'].shift(-1))
    line_mesh_df['section_length_m'] = (line_mesh_df['chainage_m'].shift(-1) - line_mesh_df['chainage_m'])
    line_mesh_df['section_elev_m'] = (line_mesh_df['elev1'].shift(-1) - line_mesh_df['elev1'])
    
    line_mesh_df['density'] = liquid_density
    line_mesh_df['velocity'] = velocity
    line_mesh_df['re_d'] = re_d
    line_mesh_df['friction_factor'] = friction_factor
    line_mesh_df['friction_loss'] = (((line_mesh_df['friction_factor'] * multiplier * (line_mesh_df['velocity'] ** 2) * liquid_density) / (2 * internal_diameter)) * line_mesh_df['section_length_m']) / 100000
    line_mesh_df['elev_loss'] = (liquid_density * 9.81 * line_mesh_df['section_elev_m'])/100000
    line_mesh_df['total_loss_bar'] = line_mesh_df['friction_loss'] + line_mesh_df['elev_loss']
    
    line_mesh_df = line_mesh_df.iloc[:-1]
    
    # Initialise columns
    line_mesh_df['p_from_bar'] = np.nan
    line_mesh_df['p_to_bar'] = np.nan

    if known == 'from_pres':

        line_mesh_df = line_mesh_df.sort_values(
            by='chainage_m',
            ascending=True
        ).reset_index(drop=True)

        # Set first known pressure
        line_mesh_df.loc[0, 'p_from_bar'] = pres

        # Step through each section
        for i in range(len(line_mesh_df)):

            p_from = line_mesh_df.loc[i, 'p_from_bar']
            
            loss = line_mesh_df.loc[i, 'total_loss_bar']

            p_to = max(p_from - loss,vapour_pres*multiplier)

            line_mesh_df.loc[i, 'p_to_bar'] = p_to

            # propagate to next row
            if i < len(line_mesh_df) - 1:
                line_mesh_df.loc[i + 1, 'p_from_bar'] = p_to

    elif known == 'to_pres':

        line_mesh_df = line_mesh_df.sort_values(
            by='chainage_m',
            ascending=False
        ).reset_index(drop=True)

        # Set downstream known pressure
        line_mesh_df.loc[0, 'p_to_bar'] = pres

        for i in range(len(line_mesh_df)):

            p_to = line_mesh_df.loc[i, 'p_to_bar']
            
            loss = line_mesh_df.loc[i, 'total_loss_bar']

            p_from = max(p_to + loss,vapour_pres*multiplier)

            line_mesh_df.loc[i, 'p_from_bar'] = p_from

            # propagate upstream
            if i < len(line_mesh_df) - 1:
                line_mesh_df.loc[i + 1, 'p_to_bar'] = p_from

        # Return to normal order
        line_mesh_df = line_mesh_df.sort_values(
            by='chainage_m',
            ascending=True
        ).reset_index(drop=True)

    return line_mesh_df

def incompressible_pres_through_network(network_df,network_xyz_df,boundaries_df,liquid_density,liquid_viscosity,vapour_pres,fluid_temp,multiplier,two_phase_layers):
    i = 0
    
    boundaries_df = boundaries_df[boundaries_df['in_service'] != False]
    known_junctions_df = boundaries_df[['junction','p_bar']]
    to_junctions = network_df['to_junction'].tolist()
    from_junctions = network_df['from_junction'].tolist()
    junctions = set(to_junctions + from_junctions)
    known_junctions = known_junctions_df['junction'].tolist()
    unknown_junctions = [item for item in junctions if item not in known_junctions]
    
    largest_mass_flow_rate = max(network_df['mdot_from_kg_per_s'].tolist())


    lst = network_df['mdot_from_kg_per_s'].tolist()
    count = sum(1 for x in lst if x != 0)

    if two_phase_layers:
        for layer in two_phase_layers:
            layer_name = layer.name().lower()
            if 'pump' in layer_name:
                pump_df = layer_to_df(layer)
                pump_from_junctions = pump_df['from_junction'].tolist()
                pump_to_junctions = pump_df['to_junction'].tolist()
                pump_junctions = set(pump_to_junctions + pump_from_junctions)
                count = count+len(pump_from_junctions)
    else:
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
                vol_flow_m_cubed_per_h = (sum(lines_connected_df['mdot_from_kg_per_s'].tolist()) / (liquid_density))*60*60
                
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
                vol_flow_m_cubed_per_h = (sum(lines_connected_df['mdot_from_kg_per_s'].tolist()) / (liquid_density))*60*60
                
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

            line_xyz_df = network_xyz_df[network_xyz_df['name']==line_name]

            if line_name in processed_lines:
                continue

            processed_lines.add(line_name)

            from_junction = row['from_junction']
            to_junction = row['to_junction']
            internal_diameter = row['diameter_m']
            roughness = row['k_mm']/1000
            length = row['length_km']*1000
            mass_flow_rate = row['mdot_from_kg_per_s']

            vol_flow_rate = mass_flow_rate / liquid_density
            area = math.pi*((internal_diameter/2)**2)
            velocity = vol_flow_rate / area
            
            froude = velocity / ((9.81*internal_diameter)**0.5)

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
            
            line_xyz_df = network_xyz_df[network_xyz_df['name']==row['name']]
            
            line_mesh_df = create_line_mesh(line_xyz_df,known,pres,mass_flow_rate,
                                            internal_diameter,roughness,multiplier,
                                            liquid_density,liquid_viscosity,
                                            vapour_pres,fluid_temp)

            network_mesh_df = pd.concat([network_mesh_df,line_mesh_df],ignore_index=True)
            
            chainages = line_mesh_df['chainage_m'].tolist()
            max_chainage = max(chainages)
            min_chainage = min(chainages)
            
            inlet_pres_mesh = line_mesh_df.loc[line_mesh_df['chainage_m'] == min_chainage,'p_from_bar'].iloc[0]
            outlet_pres_mesh = line_mesh_df.loc[line_mesh_df['chainage_m'] == max_chainage,'p_to_bar'].iloc[0]

            if junction == from_junction:
                inlet_pres = pres
                outlet_pres = outlet_pres_mesh

                df_entry = pd.DataFrame([{"junction":to_junction,"p_bar":outlet_pres}])
                known_junctions_df = pd.concat([known_junctions_df,df_entry],ignore_index=True)

            else:
                outlet_pres = pres
                inlet_pres = inlet_pres_mesh

                df_entry = pd.DataFrame([{"junction":from_junction,"p_bar":inlet_pres}])
                known_junctions_df = pd.concat([known_junctions_df,df_entry],ignore_index=True)

            line_results = {
                "line_name": row['name'],
                "p_from_bar": inlet_pres,
                "p_to_bar": outlet_pres,
                "froude": froude
            }

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

    return known_junctions_df, line_pressures_df, network_mesh_df