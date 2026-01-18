import os

import processing

from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsField, QgsVectorLayer, QgsEditorWidgetSetup, QgsDefaultValue, QgsMapLayer, QgsWkbTypes

import numpy as np
import pandas as pd
from collections import Counter

from .fitting_list_functions import *

def layer_to_df(layer):
        cols = [f.name() for f in layer.fields()]
        data = ([f[col] for col in cols] for f in layer.getFeatures())
        df = pd.DataFrame.from_records(data=data, columns = cols)
        return df

def load_df_as_layer(dataframe,df_name):
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define new folder name and path
    new_folder_name = 'working'
    new_folder_path = os.path.join(script_dir, new_folder_name)

    # Create the folder if it doesn't exist
    os.makedirs(new_folder_path, exist_ok=True)

    dataframe_file = os.path.join(new_folder_path, f'{df_name}.csv')
    dataframe.to_csv(dataframe_file,index=False)

    uri = f"file:///{dataframe_file}?delimiter=,&detectTypes=yes&geomType=none"

    results_layer = QgsVectorLayer(uri, f'{df_name}','delimitedtext')
    
    return results_layer

def corridor_summary(pipe_layers):

    merged_df = pd.DataFrame()

    for layer_name in pipe_layers:

        layer = QgsProject.instance().mapLayersByName(layer_name)[0]

        layer_df = layer_to_df(layer)

        if merged_df.empty:
            
            merged_df = layer_df
        else:
            merged_df = pd.merge(left=merged_df,right=layer_df,on='corridor_id',how='outer')
    
    return merged_df

def generate_fittings_list(assembly_list_path,assy_sheet,pipeline_feature_layer):
    
    assembly_list_df = pd.read_excel(assembly_list_path,sheet_name=assy_sheet)
    
    pipeline_feature_df = layer_to_df(pipeline_feature_layer)
    
    merged_df = pd.merge(left=pipeline_feature_df,right=assembly_list_df,on='assembly',how='left')
    
    merged_df['type_ref'] = merged_df.apply(set_type_ref, axis=1)
    merged_df['fitting_size_1'] = merged_df.apply(set_fit_size, axis=1, args=('a',))
    merged_df['fitting_size_2'] = merged_df.apply(set_fit_size, axis=1, args=('b',))
    merged_df['fitting_class_1'] = merged_df.apply(set_fit_class, axis=1, args=('a',))
    merged_df['fitting_class_2'] = merged_df.apply(set_fit_class, axis=1, args=('b',))
    merged_df['filter'] = merged_df.apply(filter_rows, axis=1)
    
    merged_df = merged_df[merged_df['filter'] != 'FILTER']
    
    merged_df = merged_df[['feat_id','service','assembly','category','type_ref','fitting_size_1','fitting_size_2','fitting_class_1','fitting_class_2']]
    
    #merged_df['fitting_size_a'] = merged_df[['fitting_size_1', 'fitting_size_2']].max(axis=1)
    #merged_df['fitting_size_b'] = merged_df[['fitting_size_1', 'fitting_size_2']].min(axis=1)
    
    #merged_df['fitting_size_b'] = merged_df['fitting_size_b'].where(merged_df[['fitting_size_1', 'fitting_size_2']].notna().all(axis=1))
    
    #merged_df['fitting_class_a'] = merged_df[['fitting_class_1', 'fitting_class_2']].max(axis=1)
    #merged_df['fitting_class_b'] = merged_df[['fitting_class_1', 'fitting_class_2']].min(axis=1)
    
    #merged_df['fitting_class_b'] = merged_df['fitting_class_b'].where(merged_df[['fitting_class_1', 'fitting_class_1']].notna().all(axis=1))
    
    #merged_df['fitting_class_a'] = merged_df['fitting_class_1']
    #merged_df['fitting_class_b'] = merged_df['fitting_class_2']
    
    #merged_df = merged_df[['feat_id','service','assembly','category','type_ref','fitting_size_a','fitting_size_b','fitting_class_a','fitting_class_b']]
    
    merged_df['item_code'] = merged_df.apply(item_code, axis=1)
    
    return merged_df
    
