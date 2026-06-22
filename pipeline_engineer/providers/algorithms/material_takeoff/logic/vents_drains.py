from scipy.signal import find_peaks as fp
import scipy.signal as s
import pandas as pd
import processing
import os
from qgis.core import QgsProject, QgsVectorLayer, QgsMapLayer

def layer_to_df(layer):
        cols = [f.name() for f in layer.fields()]
        data = ([f[col] for col in cols] for f in layer.getFeatures())
        df = pd.DataFrame.from_records(data=data, columns = cols)
        return df

def extract_xyz(line_layer,id_field,chainage,dem):
    
    points = processing.run("native:pointsalonglines", 
                                        {'INPUT':line_layer,
                                         'DISTANCE':chainage,
                                         'START_OFFSET':0,
                                         'END_OFFSET':0,
                                         'OUTPUT':'memory:'})['OUTPUT']
    
    added_geom = processing.run("qgis:exportaddgeometrycolumns", 
                                        {'INPUT':points,
                                         'CALC_METHOD':1,
                                         'OUTPUT':'memory:'})['OUTPUT']

    elevations = processing.run("native:rastersampling", 
                                        {'INPUT':added_geom,
                                         'RASTERCOPY':dem,
                                         'COLUMN_PREFIX':'elevation',
                                         'OUTPUT':'memory:'})['OUTPUT']
    
    updated_distance = processing.run("native:fieldcalculator", 
                                        {'INPUT':elevations,
                                         'FIELD_NAME':'distance',
                                         'FIELD_TYPE':0,
                                         'FIELD_LENGTH':0,
                                         'FIELD_PRECISION':0,
                                         'FORMULA':'ROUND("distance"*111111,0)',
                                         'OUTPUT':'memory:'})['OUTPUT']

    retained = processing.run("native:retainfields", 
                                        {'INPUT':updated_distance,
                                        'FIELDS':[id_field,'distance','xcoord','ycoord','elevation1'],
                                        'OUTPUT':'memory:'})['OUTPUT']
    
    return retained

def vent_drain_placer(line_layer,id_field,chainage,dem,elev_offset_lower,elev_offset_upper,vent_delta_trigger,drain_delta_trigger):

    chainage = chainage / 111111

    xyz_layer = extract_xyz(line_layer,id_field,chainage,dem)
    xyz_layer.setName('XYZ Layer')
    #QgsProject.instance().addMapLayer(xyz_layer)

    xyz_df = layer_to_df(xyz_layer)

    line_ids = set(xyz_df[id_field].tolist())

    peaks_master_df = pd.DataFrame()
    valleys_master_df = pd.DataFrame()
 
    hpv_chainage_df = pd.DataFrame()

    for line_id in line_ids:
        
        line_xyz_df = xyz_df[xyz_df[id_field] == line_id]

        min_filter = s.argrelmin(line_xyz_df["elevation1"].values,order=drain_delta_trigger)
        max_filter = s.argrelmax(line_xyz_df["elevation1"].values,order=vent_delta_trigger)

        peak_df = line_xyz_df.iloc[max_filter[0]]
        valley_df = line_xyz_df.iloc[min_filter[0]]
        
        for _,row in peak_df.iterrows():
        
            peak_chainage = row['distance']
            chainage_increment = chainage * 111111
            peak_elevation = row['elevation1']
            
            elev_diff = 0
            prev_chainage = peak_chainage
            
            try:
                while elev_diff < elev_offset_lower:
                    df_chainage = prev_chainage + chainage_increment
                    df_entry = line_xyz_df[line_xyz_df['distance'] == df_chainage]
                    
                    elevation = df_entry['elevation1'].iloc[0]
                    distance = df_entry['distance'].iloc[0]
                    
                    elev_diff = peak_elevation - elevation
                    
                    if elev_diff > elev_offset_upper:
                        df_chainage = peak_chainage
                        df_entry = line_xyz_df[line_xyz_df['distance'] == df_chainage]
                        
                        elevation = df_entry['elevation1'].iloc[0]
                        distance = df_entry['distance'].iloc[0]
                        
                        hpv_chainage_df = pd.concat([hpv_chainage_df,df_entry])
                        continue
                    
                    prev_chainage = distance
            except:
                continue
            
            hpv_chainage_df = pd.concat([hpv_chainage_df,df_entry])
        
        peaks_master_df = pd.concat([peaks_master_df,peak_df])
        valleys_master_df = pd.concat([valleys_master_df,valley_df])


    script_dir = os.path.dirname(os.path.abspath(__file__))
    peak_save_path = os.path.join(script_dir,'working','peaks.csv')
    
    peaks_master_df.to_csv(peak_save_path,index=False)
    
    layer_crs = line_layer.crs()
    
    vent_uri = (f"file:///{peak_save_path}""?delimiter=,&xField=xcoord&yField=ycoord"f"&crs={layer_crs.authid()}")

    vent_layer = QgsVectorLayer(vent_uri, 'Vents','delimitedtext')
    
    # Drain
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    drain_save_path = os.path.join(script_dir,'working','drains.csv')
    
    valleys_master_df.to_csv(drain_save_path,index=False)
    
    drain_uri = (f"file:///{drain_save_path}""?delimiter=,&xField=xcoord&yField=ycoord"f"&crs={layer_crs.authid()}")

    valley_layer = QgsVectorLayer(drain_uri, 'Drains','delimitedtext')

    merged = processing.run("native:mergevectorlayers", 
                                        {'LAYERS':[vent_layer,valley_layer],
                                         'CRS':None,
                                         'OUTPUT':'memory:'})['OUTPUT']

    rename = processing.run("native:renametablefield", 
                                        {'INPUT':merged,
                                         'FIELD':'layer',
                                         'NEW_NAME':'type',
                                         'OUTPUT':'memory:'})['OUTPUT']

    rename.setName('Vents and Drains')
    return rename