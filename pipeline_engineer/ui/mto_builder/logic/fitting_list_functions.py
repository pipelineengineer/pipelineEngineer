import os

import processing

from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsField, QgsVectorLayer, QgsEditorWidgetSetup, QgsDefaultValue, QgsMapLayer, QgsWkbTypes

import numpy as np
import pandas as pd
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

pipe_sizes_path = os.path.join(BASE_DIR, 'pipe_data', 'specifications.xlsx')

pipe_sizes_df = pd.read_excel(pipe_sizes_path,sheet_name='Pipe Size Equivalents')
pipe_classes_df = pd.read_excel(pipe_sizes_path,sheet_name='Pipe Class Equivalents')
pipe_materials_df = pd.read_excel(pipe_sizes_path,sheet_name='Pipe Materials')
filter_df = pd.read_excel(pipe_sizes_path,sheet_name='Filters')

def set_type_ref(row):

    return row['item']

def set_fit_size(row,fitting):
    direct_sizes = [
                    'corridor_size', 'header_1_size', 'header_2_size',
                    'branch_size', 'branch_1_size', 'branch_2_size',
                    'branch_3_size', 'branch_4_size'
                     ]
    
    if row[f'size_{fitting}'] in direct_sizes:
        size = row[row[f'size_{fitting}']]
        
    elif row[f'size_{fitting}'] == 'max_size':
        possible_cols = [
                            'corridor_size', 'header_1_size', 'header_2_size',
                            'branch_size', 'branch_1_size', 'branch_2_size',
                            'branch_3_size', 'branch_4_size'
                        ]

        existing_cols = [col for col in possible_cols if col in row]
        
        size = max(existing_cols)

    elif row[f'size_{fitting}'] == 'max_header_size':
        size = max(row['header_1_size'],row['header_2_size'],)
    
    else:
        size = row[f'size_{fitting}']
    
    if isinstance(size, (int, float)):
        fit_size_ceiled = max(size, row[f'size_{fitting}_ceil'])
        size = min(size, row[f'size_{fitting}_floor'])
    
    if size != row[f'size_{fitting}'] and row[f'material_{fitting}'] != 'PE100' and not pd.isna(row[f'material_{fitting}']):
        
        size = pipe_sizes_df.loc[(pipe_sizes_df['pe_size'] == size)&(pipe_sizes_df['material_a'] == 'hdpe'), 'steel_size'].iloc[0]

    return size

def set_fit_class(row,fitting):
    
    direct_classes = [
                    'corridor_class', 'header_1_class', 'header_2_class',
                    'branch_class', 'branch_1_class', 'branch_2_class',
                    'branch_3_class', 'branch_4_class'
                     ]
    
    if row[f'class_{fitting}'] in direct_classes:
        fit_class = row[row[f'class_{fitting}']]
        
    elif row[f'class_{fitting}'] == 'mode_class':
        possible_cols = [
            'corridor_class', 'header_1_class', 'header_2_class',
            'branch_class', 'branch_1_class', 'branch_2_class',
            'branch_3_class', 'branch_4_class'
        ]

        values = [
                    row[col] for col in possible_cols
                    if (
                        col in row
                        and pd.notna(row[col])
                        and str(row[col]).strip().upper() != "NULL"
                    )
                ]

        fit_class = Counter(values).most_common(1)[0][0] if values else None
        
    elif row[f'class_{fitting}'] == 'max_class':
        possible_cols = [
            'corridor_class', 'header_1_class', 'header_2_class',
            'branch_class', 'branch_1_class', 'branch_2_class',
            'branch_3_class', 'branch_4_class'
        ]
        existing_cols = [col for col in possible_cols if col in row]
        numeric_values = [v for v in row[existing_cols] if isinstance(v, (int, float))]
        fit_class = max(numeric_values) if numeric_values else None
        
    elif row[f'class_{fitting}'] == 'max_header_class':
        fit_class = max(row['header_1_class'],row['header_2_class'])
        
    else:
        fit_class = row[f'class_{fitting}']

        if isinstance(fit_class, (int, float)):
            fit_class = row[f'class_{fitting}']
        else:
            fit_class = fit_class
    
    if isinstance(fit_class, (int, float)):
        fit_class_ceiled = max(fit_class, row[f'class_{fitting}_ceil'])
        fit_class = min(fit_class_ceiled, row[f'class_{fitting}_floor'])

    if fit_class != row[f'class_{fitting}'] and row[f'material_{fitting}'] != 'PE100' and not pd.isna(row[f'material_{fitting}']):
        
        if 'ANSI' in row[f'material_{fitting}']:
            fit_class = pipe_classes_df.loc[pipe_classes_df['sdr'] == fit_class, 'ansi_class'].iloc[0]
            
        elif 'AS2129' in row[f'material_{fitting}']:
            fit_class = pipe_classes_df.loc[pipe_classes_df['sdr'] == fit_class, 'as2129_class'].iloc[0]
        
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
        
        if param == 'class':
            
            if 'ANSI' in material:
                steel_class = pipe_classes_df[['sdr'] == value, ['ansi_class']]
                
                return steel_class
                
            elif 'AS2129' in material:
                steel_class = pipe_classes_df[['sdr'] == value, ['as2129_class']]
                
                return steel_class
    
    except:
        return value