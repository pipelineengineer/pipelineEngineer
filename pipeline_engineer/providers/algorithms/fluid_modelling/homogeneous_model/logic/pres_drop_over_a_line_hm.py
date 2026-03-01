import os

import pandas as pd

from logic.main_hm import *
#from logic.beggs_brill_formula import *
from logic.dataframes_to_csv import *

def pres_drop_over_line(line_data_df, line_xyz_df,
                        liquid_density, liquid_viscosity,
                        gas_compressibility,molar_mass,gas_frac,
                        surf_tens, outlet_pres):
    
    results_df = pd.DataFrame()

    line_data_row = line_data_df.iloc[0]

    mass_flow_rate = line_data_row['mdot_from_kg_per_s']

    vol_flow_rate = mass_flow_rate / liquid_density

    pres = outlet_pres

    internal_diameter = line_data_row['diameter_m']

    line_roughness = line_data_row['k_mm']

    line_mesh_df = line_xyz_df.copy()

    print(line_mesh_df.head())

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
    
    print('LINE: ',line_mesh_df['section_id'].tolist())
    print("LINE MESH DF")
    print(line_mesh_df)
    
    for index, row in line_mesh_df.iterrows():

        length = row['section_length_m']

        elevation = row['section_elev_m']
        
        if elevation  < 0:
            
            elev_ratio = abs(elevation / length) * 1000
            
            gas_fraction = min(elev_ratio,0.5)

        bb_df_entry = homogenous_method(flow_rate=vol_flow_rate, gas_frac=gas_frac,
                       liquid_density=liquid_density,liquid_viscosity=liquid_viscosity,
                       surf_tens=surf_tens, pres=pres, gas_compressibility=gas_compressibility,molar_mass=molar_mass,
                       internal_diameter=internal_diameter,line_roughness=line_roughness,
                       length=length,elevation=elevation)
                       
        bb_df_entry['section_id'] = row['section_id']

        bb_df_entry['chainage_m'] = row['chainage_m']

        bb_df_entry['section_elev_m'] = row['section_elev_m']
        
        bb_df_entry['gas_fraction'] = gas_frac

        pres = bb_df_entry['p_from_bar'].iloc[0]

        results_df = pd.concat([results_df,bb_df_entry])
    
    results_df = results_df.sort_values(by='chainage_m',ascending=True)

    return results_df