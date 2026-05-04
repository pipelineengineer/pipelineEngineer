import os

import pandas as pd

from logic.models.single_phase import *
from logic.models.beggs_brill import *
from logic.models.gas_breakout_at_vapour_pres import *
from logic.dataframes_to_csv import *

def get_fluid_parameter(parameter,chosen_fluid,temperature,pressure):
    pres = float(pressure)
    temp = float(temperature)

    fluid_properties = []

    available_fluids = ["hgas","lgas","hydrogen","methane","water","biomethane_pure","biomethane_treated","air"]

    if chosen_fluid not in available_fluids:
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
        user_fluids_path = os.path.join(script_dir, 'user_settings','user_fluids.csv')

        print(user_fluids_path)

        user_fluids_df = pd.read_csv(user_fluids_path)
        
        chosen_fluid_name = chosen_fluid.replace(' [USER DEFINED]',"")
        
        print(chosen_fluid_name)
        
        chosen_fluid = pp.create_constant_fluid(
                                            name=chosen_fluid_name,
                                            fluid_type = user_fluids_df.loc[user_fluids_df['name'] == chosen_fluid_name, "fluid_type"].iloc[0],
                                            compressibility=user_fluids_df.loc[user_fluids_df['name'] == chosen_fluid_name, "compressibility"].iloc[0],
                                            density=user_fluids_df.loc[user_fluids_df['name'] == chosen_fluid_name, "density"].iloc[0],
                                            heat_capacity=user_fluids_df.loc[user_fluids_df['name'] == chosen_fluid_name, "heat_capacity"].iloc[0],
                                            molar_mass=user_fluids_df.loc[user_fluids_df['name'] == chosen_fluid_name, "molar_mass"].iloc[0],
                                            viscosity=user_fluids_df.loc[user_fluids_df['name'] == chosen_fluid_name, "viscosity"].iloc[0],
                                            is_gas=user_fluids_df.loc[user_fluids_df['name'] == chosen_fluid_name, "is_gas"].iloc[0]
                                        )

    net = pp.create_empty_network(fluid=chosen_fluid)
    
    if parameter == 'compressibility':
        value = net.fluid.get_compressibility(pres)
        
    elif parameter == 'density':
        value = net.fluid.get_density(temp)
        
    elif parameter == 'heat_capacity':
        value = net.fluid.get_heat_capacity(temp)
        
    elif parameter == 'molar_mass':
        value = net.fluid.get_molar_mass()
        
    elif parameter == 'viscosity':
        value = net.fluid.get_viscosity(temp)
        
    else:
        print('Parameter not available. Check spelling.')
        return
    
    return value

def pres_drop_over_line(line_data_df, line_xyz_df,
                        liquid_density, liquid_viscosity,gas_viscosity,
                        gas_compressibility,molar_mass,fluid_temp,gas_frac,
                        surf_tens, outlet_pres,flow_model):
    
    results_df = pd.DataFrame()

    line_data_row = line_data_df.iloc[0]

    mass_flow_rate = line_data_row['mdot_from_kg_per_s']

    print(line_data_row['name'])

    vol_flow_rate = mass_flow_rate / liquid_density

    pres = outlet_pres

    internal_diameter = line_data_row['diameter_m']

    line_roughness = line_data_row['k_mm']

    line_mesh_df = line_xyz_df.copy()

    line_mesh_df = line_mesh_df.sort_values('chainage_m')

    line_mesh_df['section_id'] = (
        line_mesh_df['name'].astype(str)
        + '_'
        + line_mesh_df['chainage_m'].astype(str)
        + '_'
        + line_mesh_df['chainage_m'].shift(-1).astype(str)
    )

    line_mesh_df['section_length_m'] = (
        line_mesh_df['chainage_m'].shift(-1) - line_mesh_df['chainage_m']
    )

    line_mesh_df['section_elev_m'] = (
        line_mesh_df['elev1'].shift(-1) - line_mesh_df['elev1']
    )

    line_mesh_df = line_mesh_df.iloc[:-1]

    line_mesh_df = line_mesh_df.sort_values(by='chainage_m',ascending=False)
    
    for index, row in line_mesh_df.iterrows():

        length = row['section_length_m']

        elevation = row['section_elev_m']

        if flow_model == 'Single Phase':
            
            #pipeflow_fluid_density = get_fluid_parameter(parameter='density',chosen_fluid=pipeflow_fluid,temperature=fluid_temp,pressure=fluid_pres)
            #pipeflow_fluid_viscosity = get_fluid_parameter(parameter='viscosity',chosen_fluid=pipeflow_fluid,temperature=fluid_temp,pressure=fluid_pres)
            
            df_entry = single_phase(flow_rate=vol_flow_rate, gas_frac=gas_frac,
                           liquid_density=liquid_density,liquid_viscosity=liquid_viscosity,gas_viscosity=liquid_viscosity,
                           surf_tens=surf_tens, pres=pres, gas_compressibility=gas_compressibility,molar_mass=molar_mass,fluid_temp=fluid_temp,
                           internal_diameter=internal_diameter,line_roughness=line_roughness,
                           chainage=length,elevation=elevation,downstream=False)

        elif flow_model == 'Beggs Brill':
            
            df_entry = beggs_brill_method(flow_rate=vol_flow_rate, gas_frac=gas_frac,
                           liquid_density=liquid_density,liquid_viscosity=liquid_viscosity,gas_viscosity=gas_viscosity,
                           surf_tens=surf_tens, pres=pres, gas_compressibility=gas_compressibility,molar_mass=molar_mass,fluid_temp=fluid_temp,
                           internal_diameter=internal_diameter,line_roughness=line_roughness,
                           chainage=length,elevation=elevation,include_acceleration_factor=False)

        elif flow_model == 'Gas Breakout at Vapour Pressure':
            
            df_entry = single_phase_with_gas_breakout(flow_rate=vol_flow_rate, gas_frac=gas_frac,
                           liquid_density=liquid_density,liquid_viscosity=liquid_viscosity,gas_viscosity=gas_viscosity,
                           surf_tens=surf_tens, pres=pres, gas_compressibility=gas_compressibility,molar_mass=molar_mass,fluid_temp=fluid_temp,
                           internal_diameter=internal_diameter,line_roughness=line_roughness,
                           chainage=length,elevation=elevation,downstream=False)

        df_entry['section_id'] = row['section_id']

        df_entry['chainage_m'] = row['chainage_m']

        df_entry['section_elev_m'] = row['section_elev_m']

        pres = df_entry['p_from_bar'].iloc[0]

        results_df = pd.concat([results_df,df_entry])
    
    results_df = results_df.sort_values(by='chainage_m',ascending=True)

    return results_df