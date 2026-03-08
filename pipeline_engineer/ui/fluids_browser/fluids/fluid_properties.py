import sys
import os
import pandapipes as pp
import pandas as pd


def get_fluid_properties(chosen_fluid,temperature,pressure):
    pres = float(pressure)
    temp = float(temperature)

    fluid_properties = []

    available_fluids = ["hgas","lgas","hydrogen","methane","water","biomethane_pure","biomethane_treated","air"]

    if chosen_fluid not in available_fluids:
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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

    compressibility = {"Parameter": 'Compressibility', "Value": net.fluid.get_compressibility(pres)}
    density = {"Parameter": 'Density', "Value": net.fluid.get_density(temp)}
    heat_capacity = {"Parameter": 'Heat Capacity', "Value": net.fluid.get_heat_capacity(temp)}
    molar_mass = {"Parameter": 'Molar Mass', "Value": net.fluid.get_molar_mass()}
    viscosity = {"Parameter": 'Viscosity', "Value": net.fluid.get_viscosity(temp)}

    fluid_properties.append(compressibility)
    fluid_properties.append(density)
    fluid_properties.append(heat_capacity)
    fluid_properties.append(molar_mass)
    fluid_properties.append(viscosity)

    properties_df = pd.DataFrame(fluid_properties)
    return properties_df
    
def get_fluid_parameter(parameter,chosen_fluid,temperature,pressure):
    pres = float(pressure)
    temp = float(temperature)

    net = pp.create_empty_network(fluid="lgas")

    fluid_properties = []

    net = pp.create_empty_network(fluid=f"{chosen_fluid}")
    
    if parameter == 'compressibility':
        value = net.fluid.get_compressibility(pres)
        
    elif parameter == 'density':
        value = net.fluid.get_density(temp)
        
    elif parameter == 'heat_capacity':
        value = net.fluid.get_heat_capacity(temp)
        
    elif parameter == 'molar_mass':
        value = net.fluid.get_molar_mass(temp)
        
    elif parameter == 'viscosity':
        value = net.fluid.get_viscosity(temp)
        
    else:
        print('Parameter not available. Check spelling.')
        return
    
    return value