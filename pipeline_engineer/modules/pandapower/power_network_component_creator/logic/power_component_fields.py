from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsField
from qgis.PyQt.QtCore import Qt, QVariant
import pandapower

from .function_helpers import *

power_component_fields_dict = { 
                        "Bus": ["vn_kv","name","geodata","type",
                                "zone","in_service","max_vm_pu",
                                "min_vm_pu","coords"],
                        
                        "Bus DC": ["vn_kv","name","geodata","type",
                                "zone","in_service","max_vm_pu",
                                "min_vm_pu","coords"],
                        
                        "Line": ["from_bus","to_bus","length_km",
                                 "std_type","name","geodata","in_service","df",
                                 "parallel","max_loading_percent","alpha","temperature_degree_celsius",
                                 "tdpf","wind_speed_m_per_s","wind_angle_degree","conductor_outer_diameter_m",
                                 "air_temperature_degree_celsius","reference_temperature_degree_celsius",
                                 "solar_radiation_w_per_sq_m","solar_absorptivity","emissivity",
                                 "r_theta_kelvin_per_mw","mc_joule_per_m_k"],
                        
                        "Line DC": ["from_bus_dc","to_bus_dc","length_km",
                                    "std_type","name","geodata","in_service","df",
                                    "parallel","max_loading_percent","alpha","temperature_degree_celsius",
                                    "tdpf","wind_speed_m_per_s","wind_angle_degree","conductor_outer_diameter_m",
                                    "air_temperature_degree_celsius","reference_temperature_degree_celsius",
                                    "solar_radiation_w_per_sq_m","solar_absorptivity","emissivity",
                                    "r_theta_kelvin_per_mw","mc_joule_per_m_k"],
                        
                        "Switch": ["bus","element","et","closed","type","z_ohm","name","in_ka"],
                        
                        "Load": ["bus", "p_mw", "q_mvar", "const_z_p_percent", 
                                 "const_i_p_percent", "const_z_q_percent", "const_i_q_percent", 
                                 "sn_mva", "name", "scaling", "type", "in_service", 
                                 "max_p_mw", "min_p_mw", "max_q_mvar", "min_q_mvar", "controllable"],
                        
                        "Load DC": ["bus_dc","p_dc_mw","name","in_service","scaling","type","controllable"],
                        
                        "Asymmetric Load": ["bus", "p_a_mw", "p_b_mw", 
                                            "p_c_mw", "q_a_mvar", "q_b_mvar", 
                                            "q_c_mvar", "sn_a_mva", "sn_b_mva", 
                                            "sn_c_mva", "sn_mva", "name", "scaling", 
                                            "type", "in_service"],
                        
                        "Motor": ["bus", "pn_mech_mw", "cos_phi", "name", "efficiency_percent", 
                                  "loading_percent", "scaling", "cos_phi_n", 
                                  "efficiency_n_percent", "lrc_pu", "rx", "vn_kv", "in_service"],
                        
                        "Static Generator": ["bus", "p_mw", "q_mvar", "sn_mva", "name", "scaling", 
                                             "type", "in_service", "max_p_mw", "min_p_mw", "max_q_mvar", 
                                             "min_q_mvar", "controllable", "k", "rx", "reactive_capability_curve", 
                                             "id_q_capability_characteristic", "curve_style", "generator_type", 
                                             "lrc_pu", "max_ik_ka", "kappa", "current_source"],
                        
                        "Asymmetric Static Generator": ["bus", "p_a_mw", "p_b_mw", "p_c_mw", "q_a_mvar", 
                                                        "q_b_mvar", "q_c_mvar", "sn_a_mva", "sn_b_mva", 
                                                        "sn_c_mva", "sn_mva", "name", "scaling", 
                                                        "type", "in_service"],
                        
                        "Generator": ["bus", "p_mw", "vm_pu", "sn_mva", "name", 
                                      "scaling", "type", "slack", "reactive_capability_curve", 
                                      "id_q_capability_characteristic", "curve_style", "controllable", 
                                      "slack_weight", "vn_kv", "xdss_pu", "rdss_ohm", "cos_phi", "pg_percent", 
                                      "power_station_trafo", "in_service", "max_p_mw", "min_p_mw", "max_q_mvar", 
                                      "min_q_mvar", "min_vm_pu", "max_vm_pu"],
                        
                        "External Grid":  ["bus", "vm_pu", "va_degree", "name", "in_service", 
                                           "s_sc_max_mva", "s_sc_min_mva", "rx_max", "rx_min", 
                                           "max_p_mw", "min_p_mw", "max_q_mvar", "min_q_mvar", 
                                           "r0x0_max", "x0x_max", "slack_weight", "controllable"],
                        
                        "Source DC": ["bus_dc","vm_pu","name","index","in_service","type"],
                        
                        "Transformer": ["hv_bus", "lv_bus", "std_type", "vk0_percent", 
                                        "vkr0_percent", "mag0_percent", "mag0_rx", "si0_hv_partial", 
                                        "name", "tap_pos", "in_service", "max_loading_percent", "parallel", 
                                        "df", "tap_dependency_table", "id_characteristic_table", 
                                        "tap_changer_type", "xn_ohm", "tap2_pos", "pt_percent", "oltc"],
                        
                        "Three Winding Transformer": ["hv_bus", "mv_bus", "lv_bus", "std_type", "name", 
                                                      "tap_pos", "tap_changer_type", "tap_at_star_point", 
                                                      "in_service", "max_loading_percent", "tap_dependency_table", 
                                                      "id_characteristic_table"],
                        
                        "Shunt": ["bus", "p_mw", "q_mvar", "vn_kv", "step", 
                                  "max_step", "name", "step_dependency_table", 
                                  "id_characteristic_table", "in_service"],
                        
                        "Impedance": ["from_bus", "to_bus", "rft_pu", 
                                      "xft_pu", "sn_mva", "rtf_pu", "xtf_pu", 
                                      "name", "in_service", "rft0_pu", "xft0_pu", 
                                      "rtf0_pu", "xtf0_pu", "gf_pu", "bf_pu", "gt_pu", 
                                      "bt_pu", "gf0_pu", "bf0_pu", "gt0_pu", "bt0_pu"],
                        
                        "Ward": ["bus", "ps_mw", "qs_mvar", "pz_mw", "qz_mvar", "name", "in_service"],
                        
                        "Extended Ward": ["bus", "ps_mw", "qs_mvar", "pz_mw", "qz_mvar", 
                                          "r_ohm", "x_ohm", "vm_pu", "in_service", 
                                          "name", "slack_weight"],
                        
                        "HV DC Link / DC Line": ["from_bus", "to_bus", "p_mw", "loss_percent", "loss_mw", 
                                                 "vm_from_pu", "vm_to_pu", "name", "in_service", 
                                                 "max_p_mw", "min_q_from_mvar", "min_q_to_mvar", 
                                                 "max_q_from_mvar", "max_q_to_mvar"],
                        
                        "Measurement": ["meas_type", "element_type", "value", 
                                        "std_dev", "element", "side", 
                                        "check_existing", "name"],
                        
                        "Storage": ["bus", "p_mw", "max_e_mwh", "q_mvar", "sn_mva", 
                                    "soc_percent", "min_e_mwh", "name", "scaling", 
                                    "type", "in_service", "max_p_mw", "min_p_mw", "max_q_mvar", 
                                    "min_q_mvar", "controllable"],
                        
                        "Static Var Compensator (SVC)": ["bus", "x_l_ohm", "x_cvar_ohm", "set_vm_pu", 
                                                         "thyristor_firing_angle_degree", "name", 
                                                         "controllable", "in_service", "min_angle_degree", 
                                                         "max_angle_degree"],
                        
                        "Thyristor-Controlled Series Capacitor (TCSC)": ["from_bus", "to_bus", "x_l_ohm", 
                                                                         "x_cvar_ohm", "set_p_to_mw", 
                                                                         "thyristor_firing_angle_degree", "name", 
                                                                         "controllable", "in_service", "min_angle_degree", 
                                                                         "max_angle_degree"],
                        
                        "Static Synchronous Compensator (SSC)": ["bus", "r_ohm", "x_ohm", "set_vm_pu", 
                                                                 "vm_internal_pu", "va_internal_degree", 
                                                                 "name", "controllable", "in_service"],
                        
                        "Voltage Source Converter (VSC)": ["bus", "bus_dc", "r_ohm", "x_ohm", "r_dc_ohm", 
                                                           "pl_dc_mw", "control_mode_ac", "control_value_ac", "control_mode_dc", 
                                                           "control_value_dc", "name", "controllable", "in_service"],
                        
                        "Stacked Voltage Source Converter (VSC Stacked)":  ["bus", "bus_dc_plus", "bus_dc_minus", "r_ohm", 
                                                                            "x_ohm", "r_dc_ohm", "pl_dc_mw", "control_mode_ac", 
                                                                            "control_value_ac", "control_mode_dc", "control_value_dc", 
                                                                            "name", "controllable", "in_service"]
 
                         }


power_component_geometries_dict = {
    # Buses
    "Bus": ['Point'],
    "Bus DC": ['Point'],

    # Branches
    "Line": ['LineString'],
    "Line DC": ['LineString'],
    "Transformer": ['LineString'],
    "Three Winding Transformer": ['LineString'],
    "HV DC Link / DC Line": ['LineString'],
    "Impedance": ['LineString'],
    "Thyristor-Controlled Series Capacitor (TCSC)": ['LineString'],

    # Switches (can be points or short lines)
    "Switch": ['Point', 'LineString'],

    # Injection / Load points
    "Load": ['Point'],
    "Load DC": ['Point'],
    "Asymmetric Load": ['Point'],
    "Motor": ['Point'],
    "Static Generator": ['Point'],
    "Asymmetric Static Generator": ['Point'],
    "Generator": ['Point'],
    "External Grid": ['Point'],
    "Source DC": ['Point'],

    # Shunts / Wards / Compensators / Storage
    "Shunt": ['Point'],
    "Ward": ['Point'],
    "Extended Ward": ['Point'],
    "Storage": ['Point'],
    "Static Var Compensator (SVC)": ['Point'],
    "Static Synchronous Compensator (SSC)": ['Point'],
    "Voltage Source Converter (VSC)": ['Point'],
    "Stacked Voltage Source Converter (VSC Stacked)": ['Point'],

    # Measurement points
    "Measurement": ['Point']
}

power_field_types =  [
    QgsField("vn_kv", QVariant.Double),
    QgsField("name", QVariant.String),
    QgsField("geodata", QVariant.String),
    QgsField("type", QVariant.String),
    QgsField("zone", QVariant.String),
    QgsField("in_service", QVariant.Bool),
    QgsField("max_vm_pu", QVariant.Double),
    QgsField("min_vm_pu", QVariant.Double),
    QgsField("coords", QVariant.String),
    QgsField("from_bus", QVariant.String),
    QgsField("to_bus", QVariant.String),
    QgsField("from_bus_dc", QVariant.String),
    QgsField("to_bus_dc", QVariant.String),
    QgsField("length_km", QVariant.Double),
    QgsField("std_type", QVariant.String),
    QgsField("df", QVariant.Double),
    QgsField("parallel", QVariant.Int),
    QgsField("max_loading_percent", QVariant.Double),
    QgsField("alpha", QVariant.Double),
    QgsField("temperature_degree_celsius", QVariant.Double),
    QgsField("tdpf", QVariant.Double),
    QgsField("wind_speed_m_per_s", QVariant.Double),
    QgsField("wind_angle_degree", QVariant.Double),
    QgsField("conductor_outer_diameter_m", QVariant.Double),
    QgsField("air_temperature_degree_celsius", QVariant.Double),
    QgsField("reference_temperature_degree_celsius", QVariant.Double),
    QgsField("solar_radiation_w_per_sq_m", QVariant.Double),
    QgsField("solar_absorptivity", QVariant.Double),
    QgsField("emissivity", QVariant.Double),
    QgsField("r_theta_kelvin_per_mw", QVariant.Double),
    QgsField("mc_joule_per_m_k", QVariant.Double),
    QgsField("bus", QVariant.String),
    QgsField("element", QVariant.Int),
    QgsField("et", QVariant.String),
    QgsField("closed", QVariant.Bool),
    QgsField("z_ohm", QVariant.Double),
    QgsField("in_ka", QVariant.Double),
    QgsField("p_mw", QVariant.Double),
    QgsField("q_mvar", QVariant.Double),
    QgsField("const_z_p_percent", QVariant.Double),
    QgsField("const_i_p_percent", QVariant.Double),
    QgsField("const_z_q_percent", QVariant.Double),
    QgsField("const_i_q_percent", QVariant.Double),
    QgsField("sn_mva", QVariant.Double),
    QgsField("scaling", QVariant.Double),
    QgsField("max_p_mw", QVariant.Double),
    QgsField("min_p_mw", QVariant.Double),
    QgsField("max_q_mvar", QVariant.Double),
    QgsField("min_q_mvar", QVariant.Double),
    QgsField("controllable", QVariant.Bool),
    QgsField("p_dc_mw", QVariant.Double),
    QgsField("p_a_mw", QVariant.Double),
    QgsField("p_b_mw", QVariant.Double),
    QgsField("p_c_mw", QVariant.Double),
    QgsField("q_a_mvar", QVariant.Double),
    QgsField("q_b_mvar", QVariant.Double),
    QgsField("q_c_mvar", QVariant.Double),
    QgsField("sn_a_mva", QVariant.Double),
    QgsField("sn_b_mva", QVariant.Double),
    QgsField("sn_c_mva", QVariant.Double),
    QgsField("pn_mech_mw", QVariant.Double),
    QgsField("cos_phi", QVariant.Double),
    QgsField("efficiency_percent", QVariant.Double),
    QgsField("loading_percent", QVariant.Double),
    QgsField("cos_phi_n", QVariant.Double),
    QgsField("efficiency_n_percent", QVariant.Double),
    QgsField("lrc_pu", QVariant.Double),
    QgsField("rx", QVariant.Double),
    QgsField("vn_kv", QVariant.Double),
    QgsField("k", QVariant.Double),
    QgsField("reactive_capability_curve", QVariant.String),
    QgsField("id_q_capability_characteristic", QVariant.Int),
    QgsField("curve_style", QVariant.String),
    QgsField("generator_type", QVariant.String),
    QgsField("max_ik_ka", QVariant.Double),
    QgsField("kappa", QVariant.Double),
    QgsField("current_source", QVariant.Bool),
    QgsField("vm_pu", QVariant.Double),
    QgsField("slack", QVariant.Bool),
    QgsField("slack_weight", QVariant.Double),
    QgsField("xdss_pu", QVariant.Double),
    QgsField("rdss_ohm", QVariant.Double),
    QgsField("pg_percent", QVariant.Double),
    QgsField("power_station_trafo", QVariant.String),
    QgsField("min_vm_pu", QVariant.Double),
    QgsField("max_vm_pu", QVariant.Double),
    QgsField("va_degree", QVariant.Double),
    QgsField("s_sc_max_mva", QVariant.Double),
    QgsField("s_sc_min_mva", QVariant.Double),
    QgsField("rx_max", QVariant.Double),
    QgsField("rx_min", QVariant.Double),
    QgsField("r0x0_max", QVariant.Double),
    QgsField("x0x_max", QVariant.Double),
    QgsField("vm_pu", QVariant.Double),
    QgsField("hv_bus", QVariant.String),
    QgsField("mv_bus", QVariant.String),
    QgsField("lv_bus", QVariant.String),
    QgsField("vk0_percent", QVariant.Double),
    QgsField("vkr0_percent", QVariant.Double),
    QgsField("mag0_percent", QVariant.Double),
    QgsField("mag0_rx", QVariant.Double),
    QgsField("si0_hv_partial", QVariant.Double),
    QgsField("tap_pos", QVariant.Double),
    QgsField("tap2_pos", QVariant.Double),
    QgsField("pt_percent", QVariant.Double),
    QgsField("oltc", QVariant.Bool),
    QgsField("tap_at_star_point", QVariant.Bool),
    QgsField("step", QVariant.Int),
    QgsField("max_step", QVariant.Int),
    QgsField("rft_pu", QVariant.Double),
    QgsField("xft_pu", QVariant.Double),
    QgsField("rtf_pu", QVariant.Double),
    QgsField("xtf_pu", QVariant.Double),
    QgsField("rft0_pu", QVariant.Double),
    QgsField("xft0_pu", QVariant.Double),
    QgsField("rtf0_pu", QVariant.Double),
    QgsField("xtf0_pu", QVariant.Double),
    QgsField("gf_pu", QVariant.Double),
    QgsField("bf_pu", QVariant.Double),
    QgsField("gt_pu", QVariant.Double),
    QgsField("bt_pu", QVariant.Double),
    QgsField("gf0_pu", QVariant.Double),
    QgsField("bf0_pu", QVariant.Double),
    QgsField("gt0_pu", QVariant.Double),
    QgsField("bt0_pu", QVariant.Double),
    QgsField("r_ohm", QVariant.Double),
    QgsField("x_ohm", QVariant.Double),
    QgsField("vm_pu", QVariant.Double),
    QgsField("loss_percent", QVariant.Double),
    QgsField("loss_mw", QVariant.Double),
    QgsField("vm_from_pu", QVariant.Double),
    QgsField("vm_to_pu", QVariant.Double),
    QgsField("min_q_from_mvar", QVariant.Double),
    QgsField("min_q_to_mvar", QVariant.Double),
    QgsField("max_q_from_mvar", QVariant.Double),
    QgsField("max_q_to_mvar", QVariant.Double),
    QgsField("meas_type", QVariant.String),
    QgsField("element_type", QVariant.String),
    QgsField("value", QVariant.Double),
    QgsField("std_dev", QVariant.Double),
    QgsField("element", QVariant.Int),
    QgsField("side", QVariant.String),
    QgsField("check_existing", QVariant.Bool),
    QgsField("max_e_mwh", QVariant.Double),
    QgsField("soc_percent", QVariant.Double),
    QgsField("min_e_mwh", QVariant.Double),
    QgsField("max_p_mw", QVariant.Double),
    QgsField("min_p_mw", QVariant.Double),
    QgsField("max_q_mvar", QVariant.Double),
    QgsField("min_q_mvar", QVariant.Double),
    QgsField("x_l_ohm", QVariant.Double),
    QgsField("x_cvar_ohm", QVariant.Double),
    QgsField("set_vm_pu", QVariant.Double),
    QgsField("thyristor_firing_angle_degree", QVariant.Double),
    QgsField("vm_internal_pu", QVariant.Double),
    QgsField("va_internal_degree", QVariant.Double),
    QgsField("r_dc_ohm", QVariant.Double),
    QgsField("pl_dc_mw", QVariant.Double),
    QgsField("control_mode_ac", QVariant.String),
    QgsField("control_value_ac", QVariant.Double),
    QgsField("control_mode_dc", QVariant.String),
    QgsField("control_value_dc", QVariant.Double),
                ]

def create_junction_layer_from_existing(layer,fields_to_keep):
    network_vertices = processing.run("native:extractspecificvertices", 
                                        {'INPUT':layer,
                                        'VERTICES':'0,-1',
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    delete_dupes = processing.run("native:deleteduplicategeometries", 
                                    {'INPUT':network_vertices,
                                    'OUTPUT':'memory:'})['OUTPUT']

    name_added = processing.run("native:fieldcalculator", 
                                {'INPUT':delete_dupes,
                                    'FIELD_NAME':'name',
                                    'FIELD_TYPE':2, # Text
                                    'FIELD_LENGTH':0,
                                    'FIELD_PRECISION':0,
                                    'FORMULA':"CONCAT('Junction ',$id)",
                                    'OUTPUT':'memory:'})['OUTPUT']
    
    fields_to_keep.append('name')

    dropped = processing.run("native:retainfields", 
                            {'INPUT':name_added,
                            'FIELDS':fields_to_keep,
                            'OUTPUT':'memory:'})['OUTPUT']

    QgsProject.instance().addMapLayer(dropped)

    return dropped

def create_pipe_layer_from_existing(layer,fields_to_keep,junction_layer,component_name_field):
    layer = processing.run("native:renametablefield", 
            {'INPUT':layer,
            'FIELD':component_name_field,
            'NEW_NAME':'name',
            'OUTPUT':'memory:'})['OUTPUT']

    from_vertices = processing.run("native:extractspecificvertices", 
                                        {'INPUT':layer,
                                        'VERTICES':'0',
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    attach_from_node_id = processing.run("native:joinattributesbylocation", 
                                            {'INPUT':from_vertices,
                                            'PREDICATE':[2], # Equals
                                            'JOIN':junction_layer,
                                            'JOIN_FIELDS':['name'],
                                            'METHOD':0,
                                            'DISCARD_NONMATCHING':False,
                                            'PREFIX':'',
                                            'OUTPUT':'memory:'})['OUTPUT']
    
    rename_from = processing.run("native:renametablefield", 
                                    {'INPUT':attach_from_node_id,
                                    'FIELD':'name_2',
                                    'NEW_NAME':'from_junction',
                                    'OUTPUT':'memory:'})['OUTPUT']
    
    to_vertices = processing.run("native:extractspecificvertices", 
                                        {'INPUT':layer,
                                        'VERTICES':'-1',
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    attach_to_node_id = processing.run("native:joinattributesbylocation", 
                                            {'INPUT':to_vertices,
                                            'PREDICATE':[2], # Equals
                                            'JOIN':junction_layer,
                                            'JOIN_FIELDS':['name'],
                                            'METHOD':0,
                                            'DISCARD_NONMATCHING':False,
                                            'PREFIX':'',
                                            'OUTPUT':'memory:'})['OUTPUT']
    
    rename_to = processing.run("native:renametablefield", 
                                    {'INPUT':attach_to_node_id,
                                    'FIELD':'name_2',
                                    'NEW_NAME':'to_junction',
                                    'OUTPUT':'memory:'})['OUTPUT']
    
    join_from_jct = processing.run("native:joinattributestable", 
                                    {'INPUT':layer,
                                        'FIELD':'name',
                                        'INPUT_2':rename_from,
                                        'FIELD_2':'name',
                                        'FIELDS_TO_COPY':['from_junction'],
                                        'METHOD':1,
                                        'DISCARD_NONMATCHING':False,
                                        'PREFIX':'',
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    join_to_jct = processing.run("native:joinattributestable", 
                                    {'INPUT':join_from_jct,
                                        'FIELD':'name',
                                        'INPUT_2':rename_to,
                                        'FIELD_2':'name',
                                        'FIELDS_TO_COPY':['to_junction'],
                                        'METHOD':1,
                                        'DISCARD_NONMATCHING':False,
                                        'PREFIX':'',
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    fields_to_keep.extend(['name','from_junction','to_junction'])

    dropped = processing.run("native:retainfields", 
                                {'INPUT':join_to_jct,
                                'FIELDS':fields_to_keep,
                                'OUTPUT':'memory:'})['OUTPUT']

    return dropped
            
def create_component_with_junctions_from_existing(layer,fields_to_keep,component_name_field,junction_layer):
        layer = processing.run("native:renametablefield", 
                                        {'INPUT':layer,
                                        'FIELD':component_name_field,
                                        'NEW_NAME':'name',
                                        'OUTPUT':'memory:'})['OUTPUT']

        nearest_joined = processing.run("native:joinbynearest", 
                                        {'INPUT':layer,
                                        'INPUT_2':junction_layer,
                                        'FIELDS_TO_COPY':['name'],
                                        'DISCARD_NONMATCHING':False,
                                        'PREFIX':'',
                                        'NEIGHBORS':1,
                                        'MAX_DISTANCE':None,
                                        'OUTPUT':'memory:'})['OUTPUT']
        
        rename_jct = processing.run("native:renametablefield", 
                                        {'INPUT':nearest_joined,
                                        'FIELD':'name_2',
                                        'NEW_NAME':'junction',
                                        'OUTPUT':'memory:'})['OUTPUT']
        
        fields_to_keep.extend(['name','junction'])

        dropped = processing.run("native:retainfields", 
                                    {'INPUT':rename_jct,
                                    'FIELDS':fields_to_keep,
                                    'OUTPUT':'memory:'})['OUTPUT']
        
        return dropped

def create_component_from_existing(layer,component_name_field,fields_to_keep):
    layer = processing.run("native:renametablefield", 
                                        {'INPUT':layer,
                                        'FIELD':component_name_field,
                                        'NEW_NAME':'name',
                                        'OUTPUT':'memory:'})['OUTPUT']


    dropped = processing.run("native:retainfields", 
                                {'INPUT':layer,
                                'FIELDS':fields_to_keep,
                                'OUTPUT':'memory:'})['OUTPUT']
    
    return dropped

def add_fields_through_provider(layer,fields,junction_layer):
    # 3. Add the fields to the memory layer
    provider = layer.dataProvider()
    provider.addAttributes(fields)

    # 4. Update the layer’s fields so QGIS recognizes them
    layer.updateFields()

    junction_fields = ["junction","controlled_junction", "flow_junction", "from_junction", "return_junction", "to_junction"]

    common_values = set(fields) & set(junction_fields)

    for value in common_values:
        setup_value_relation(layer=layer,field_name=value,junction_layer=junction_layer)