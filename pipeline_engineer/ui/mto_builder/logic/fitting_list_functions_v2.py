import os

import processing

from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsField, QgsVectorLayer, QgsEditorWidgetSetup, QgsDefaultValue, QgsMapLayer, QgsWkbTypes

import numpy as np
import pandas as pd
from collections import Counter

import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

pipe_sizes_path = os.path.join(BASE_DIR, 'pipe_data', 'specifications.xlsx')

pipe_sizes_df = pd.read_excel(pipe_sizes_path,sheet_name='Pipe Size Equivalents')
pipe_classes_df = pd.read_excel(pipe_sizes_path,sheet_name='Pipe Class Equivalents')
pipe_materials_df = pd.read_excel(pipe_sizes_path,sheet_name='Pipe Materials')
filter_df = pd.read_excel(pipe_sizes_path,sheet_name='Filters')

pipe_classes_df = pipe_classes_df.melt(
                            id_vars='pn_rating',
                            var_name='material',
                            value_name='feat_class'
                        )

def row_attributes_as_df(row):
    
    lines = ['corridor', 'header_1', 'header_2','branch', 'branch_1', 'branch_2','branch_3', 'branch_4']

    lines_in_layer = []

    columns = list(row.index)

    for combabula_state_forest in lines:
        
        if f'{combabula_state_forest}_material' in columns:
            
            lines_in_layer.append(combabula_state_forest)


    out = pd.DataFrame([
                            {
                                "line": line,
                                "material": row[f"{line}_material"],
                                "size": row[f"{line}_size"],
                                "feat_class": row[f"{line}_class"],
                            }
                            for line in lines_in_layer
                        ])

    return out


def set_type_ref(row):

    return row['item']

def set_fit_size(row,fitting):
    direct_sizes = [
                    'corridor_size', 'header_1_size', 'header_2_size',
                    'branch_size', 'branch_1_size', 'branch_2_size',
                    'branch_3_size', 'branch_4_size'
                     ]
    
    if pd.isna(row[f'size_{fitting}']):
        
        fit_size = None
        
        return fit_size
    
    if isinstance(row[f'size_{fitting}'],(int,float)):
        
        return row[f'size_{fitting}']

    line_feature = re.sub('_size', '', row[f'size_{fitting}']) 

    
    row_attributes_df = row_attributes_as_df(row)
    row_attributes_df = row_attributes_df[~row_attributes_df['size'].str.contains('NULL', na=False)]

    if 'branch' in row[f'size_{fitting}']:
        
        row_attributes_df = row_attributes_df[row_attributes_df['line'].str.contains('branch', na=False)]
        
    elif 'header' in row[f'size_{fitting}']:
        
        row_attributes_df = row_attributes_df[row_attributes_df['line'].str.contains('header', na=False)]

    feature_sizes = row_attributes_df['size'].tolist()

    if 'max' in row[f'size_{fitting}']:
        
        nom_size = max(feature_sizes)
    
    elif 'min' in row[f'size_{fitting}']:
        
        nom_size = max(feature_sizes)
        
    elif 'mode' in row[f'size_{fitting}']:
        
        nom_size = max(feature_sizes)
    
    elif line_feature in row[f'size_{fitting}']:
        
        nom_size = row_attributes_df.loc[row_attributes_df['line'] == line_feature, 'size'].iloc[0]
    
    if pd.isna(row[f'material_{fitting}']):
        
        fit_size = nom_size
    
        return fit_size
    
    fitting_material_type = pipe_materials_df.loc[
                        pipe_materials_df['material'] == row[f'material_{fitting}'],
                        'material_type'].iloc[0]

    feature_material = row_attributes_df.loc[row_attributes_df['size'] == nom_size, 'material'].iloc[0]

    try:
        line_material_type = pipe_materials_df.loc[
                        pipe_materials_df['material'] == feature_material,
                        'material_type'].iloc[0]
    
    except:
        print(feature_material)
        print(nom_size)
        print(row_attributes_df)
        line_material_type = pipe_materials_df.loc[
                        pipe_materials_df['material'] == feature_material,
                        'material_type'].iloc[0]

    if fitting_material_type != line_material_type:
        
        fit_size = pipe_sizes_df[
                                 (pipe_sizes_df['material_a'] == line_material_type &
                                  pipe_sizes_df['size_a'] == nom_size &
                                  pipe_sizes_df['material_b'] == fitting_material_type),
                                 'size_b'].iloc[0]
    
    else:
        
        fit_size = nom_size
    
    return fit_size

def set_fit_class(row,fitting):
    
    direct_classes = [
                    'corridor_class', 'header_1_class', 'header_2_class',
                    'branch_class', 'branch_1_class', 'branch_2_class',
                    'branch_3_class', 'branch_4_class'
                     ]
    
    row_attributes_df = row_attributes_as_df(row)
    
    row_attributes_df = row_attributes_df[
                                            row_attributes_df['material'].notna() &
                                            (row_attributes_df['material'] != 'NULL')
                                        ]
    
    row_attributes_df = pd.merge(row_attributes_df,pipe_classes_df,how = 'left', on = ['material','feat_class'])
    
    pn_rating_list = row_attributes_df['pn_rating'].tolist()
    
    if row[f'class_{fitting}'] in direct_classes:
        
        line_feature = re.sub('_class', '', row[f'class_{fitting}'])
        
        fitting_pn_rating = row_attributes_df.loc[
                                (row_attributes_df['line'] == line_feature),
                                'pn_rating'
                                ].iloc[0]
        
    elif row[f'class_{fitting}'] == 'mode_class':
        
        fitting_pn_rating = Counter(pn_rating_list).most_common(1)[0][0]
        
    elif row[f'class_{fitting}'] == 'max_class':

        fitting_pn_rating = max(pn_rating_list)
        
    elif row[f'class_{fitting}'] == 'max_header_class':
        max_pn_rating = max(row['header_1_class'],row['header_2_class'])
        
        header_df = row_attributes_df.loc[
            row_attributes_df['line'].isin(['header_1', 'header_2'])
        ]
        
        header_pn_rating_list = header_df['pn_rating'].tolist()
        
        fitting_pn_rating = max(max_pn_rating)
        
    else:
        fit_class = row[f'class_{fitting}']
        
        if pd.isna(fit_class):
            
            return fit_class
        
        fitting_pn_rating = pipe_classes_df.loc[
                                ((pipe_classes_df['feat_class'] == row[f'class_{fitting}']) &
                                 (pipe_classes_df['material'] == row[f'material_{fitting}'])),
                                'pn_rating'
                                ].iloc[0]
        
    
    if not pd.isna(row[f'class_{fitting}_ceil']):
        
        pn_ceil_applied = min(fitting_pn_rating,row[f'class_{fitting}_ceil'])
        fitting_pn_rating = pn_ceil_applied
        
    if not pd.isna(row[f'class_{fitting}_floor']):
        pn_floor_applied = max(fitting_pn_rating,row[f'class_{fitting}_floor'])
        fitting_pn_rating = pn_floor_applied
        
    if pd.isna(fitting_pn_rating):
        
        fit_class = fitting_pn_rating
        
        return fit_class

    feature_material = row_attributes_df.loc[row_attributes_df['pn_rating'] == fitting_pn_rating, 'material'].iloc[0]

    fitting_material = row[f'material_{fitting}']

    if pd.isna(fitting_material):
        
        fitting_material = feature_material
    
    try:
        fit_class = pipe_classes_df.loc[
            ((pipe_classes_df['pn_rating'] == fitting_pn_rating) &
             (pipe_classes_df['material'] == fitting_material)),
            'feat_class'
            ].iloc[0]

    except:
        print(fitting_pn_rating)
        print(fitting_material)

        fit_class = pipe_classes_df.loc[
                        ((pipe_classes_df['pn_rating'] == fitting_pn_rating) &
                         (pipe_classes_df['material'] == fitting_material)),
                        'feat_class'
                        ].iloc[0]
       
    
    return fit_class

def filter_rows(row):
    
    item = row['type_ref']
    
    item_filter_df = filter_df[filter_df['item'] == item]
    
    for index, filter_row in item_filter_df.iterrows():
        
        variable_a = row[filter_row['variable_a']]
        condition = filter_row['condition']
        variable_b = row[filter_row['variable_b']]
        
        if condition == 'equal' and variable_a == variable_b:
            return 'FILTER'
        elif condition == 'does not equal' and variable_a != variable_b:
            return 'FILTER'
        
        try:
            if condition == 'greater than' and variable_a > variable_b:
                return 'FILTER'
            elif condition == 'greater than or equal to' and variable_a >= variable_b:
                return 'FILTER'
            elif condition == 'less than' and variable_a < variable_b:
                return 'FILTER'
            elif condition == 'less than or equal to' and variable_a <= variable_b:
                return 'FILTER'
            elif condition == 'blank' and variable_a == None:
                return 'FILTER'
        except:
            pass
        
    
    return None
    

def item_code(row):
    # Helper to format numbers like Excel: drop .0 if integer
    def fmt(x):
        if pd.isna(x) or x == '':
            return ''
        elif isinstance(x, (int, float)) and x == int(x):
            return str(int(x))
        else:
            return str(x)
    
    # Join fitting sizes with 'x', ignoring blanks
    fitting_size = 'x'.join([fmt(row['fitting_size_1']), fmt(row['fitting_size_2'])])
    fitting_size = fitting_size.strip('x')  # remove x if any side was blank
    
    # Join type_ref, fitting_size, and fitting_class columns with '-', ignoring blanks
    parts = [fmt(row['type_ref']), fitting_size, fmt(row['fitting_class_1']), fmt(row['fitting_class_2'])]
    return '-'.join([p for p in parts if p != ''])

def material_equivalent(param,value,material,column):
    
    mat_type = pipe_materials_df[['material']==f'material_{column}','material_type']
    
    try:
        if param == 'size':
            
            if mat_type == 'steel':
                steel_size = pipe_sizes_df[['material_a'] == 'hdpe',['pe_size'] == value, 'steel_size']
                
                return steel_size
        
        if param == 'feat_class':
            
            if 'ANSI' in material:
                steel_class = pipe_classes_df[['sdr'] == value, ['ansi_class']]
                
                return steel_class
                
            elif 'AS2129' in material:
                steel_class = pipe_classes_df[['sdr'] == value, ['as2129_class']]
                
                return steel_class
    
    except:
        return value