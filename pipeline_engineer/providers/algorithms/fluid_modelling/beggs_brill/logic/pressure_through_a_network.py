import os
import pandas as pd

from logic.pres_drop_over_a_line import *

def pressures_through_a_network(line_data_df, line_xyz_df,grids_df,pump_df,
                            liquid_density, liquid_viscosity,
                            gas_density, gas_viscosity,
                            surf_tens,gas_fraction):

    known_pressures_df = grids_df[['junction','p_bar']]

    i = 0
    updated_lines_df = pd.DataFrame()

    master_results_df = pd.DataFrame()

    if pump_df.empty:
        pump_from_nodes = []
        pump_to_nodes = []
        pump_curves = []
    else:
        pump_from_nodes = pump_df['from_junction'].tolist()
        pump_to_nodes = pump_df['to_junction'].tolist()
        pump_curves = pump_df['std_type'].tolist()

    while i < len(known_pressures_df):
        
        row = known_pressures_df.iloc[i]
        junction = row['junction']
        junction_pres = row['p_bar']

        lines_connected_df = line_data_df[line_data_df['to_junction'] == junction]

        if junction in pump_to_nodes:
            jct_index = pump_to_nodes.index(junction)
            
            from_node = pump_from_nodes[jct_index]
            pump_curve = pump_curves[jct_index]
            
            lines_connected_df = line_data_df[line_data_df['from_junction'] == junction]
            vol_flow_m_cubed_per_h = (sum(lines_connected_df['mdot_from_kg_per_s'].tolist()) / (((1-gas_fraction)*liquid_density + gas_fraction*gas_density) / 2))*60*60
            
            if pump_curve == 'P3':
                from_jct_pres = junction_pres - (-0.00001*vol_flow_m_cubed_per_h+5)
                
            elif pump_curve == 'P2':
                from_jct_pres = junction_pres - (-3.125e-4*(vol_flow_m_cubed_per_h**2) - 1.25e-2*(vol_flow_m_cubed_per_h) + 10)
                
            elif pump_curve == 'P1':
                from_jct_pres = junction_pres - (-2.08e-4*(vol_flow_m_cubed_per_h**2) - 3.33e-3*(vol_flow_m_cubed_per_h) + 6.1)

            found_pressures_df = pd.DataFrame({"junction": [from_node], "p_bar": [from_jct_pres]})
            
            known_pressures_df = pd.concat(
                [known_pressures_df, found_pressures_df],
                ignore_index=True
            )

        for _, line_row in lines_connected_df.iterrows():
            
            line_name = line_row['name']

            print(line_name)

            from_junction = line_row['from_junction']

            selected_line_df = line_data_df[line_data_df['name'] == line_name].copy()
            selected_line_df = selected_line_df.reset_index(drop=True)
            selected_xyz_df = line_xyz_df[line_xyz_df['name']==line_name].copy()

            #selected_xyz_df.to_clipboard()

            pres_drop_df = pres_drop_over_line(
                line_data_df=selected_line_df, line_xyz_df=selected_xyz_df,
                liquid_density=liquid_density, liquid_viscosity=liquid_viscosity,
                gas_density=gas_density, gas_viscosity=gas_viscosity,
                surf_tens=surf_tens, gas_fraction=gas_fraction,
                outlet_pres=junction_pres
            )

            pres_drop_df.loc[0, "name"] = line_row['name']
            pres_drop_df.loc[0, "from_junction"] = line_row['from_junction']
            pres_drop_df.loc[0, "to_junction"] = line_row['to_junction']

            master_results_df = pd.concat([master_results_df,pres_drop_df],ignore_index=True)

            selected_line_df.loc[0, "to_junction"] = line_row['to_junction']
            selected_line_df.loc[0, "from_junction"] = line_row['from_junction']
            selected_line_df.loc[0, "to_junction"] = line_row['to_junction']

            line_from_junction_pres = pres_drop_df["p_from_bar"].iloc[0]
            selected_line_df.loc[0, "p_from_bar"] = line_from_junction_pres
            selected_line_df.loc[0, "p_to_bar"] = junction_pres

            updated_lines_df = pd.concat([updated_lines_df,selected_line_df],ignore_index=True)

            # Append new junction to process
            found_pressures_df = pd.DataFrame({"junction": [from_junction], "p_bar": [line_from_junction_pres]})
            
            is_present = found_pressures_df['junction'].isin(known_pressures_df['junction'])
            
            print(is_present)
            
            if not is_present.any():
            
                known_pressures_df = pd.concat(
                    [known_pressures_df, found_pressures_df],
                    ignore_index=True
                )

            if selected_line_df['name'].isna().any():
                break

        i += 1

    return known_pressures_df, updated_lines_df,master_results_df

