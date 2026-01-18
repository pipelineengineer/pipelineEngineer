import os

import processing

from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsField, QgsVectorLayer, QgsEditorWidgetSetup, QgsDefaultValue, QgsMapLayer, QgsWkbTypes

import numpy as np
import pandas as pd
from collections import Counter


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

pipe_sizes_path = os.path.join(BASE_DIR, 'pipe_data', 'pipe_sizes.csv')
pipe_classes_path = os.path.join(BASE_DIR, 'pipe_data', 'pipe_classes.csv')

pipe_sizes_df = pd.read_csv(pipe_sizes_path)
pipe_classes_df = pd.read_csv(pipe_classes_path)

def set_type_ref(row):
    if row['item'] == 'TEE' and row['branch_size'] < max(row['header_1_size'],row['header_2_size']):
        return 'RED_TEE'
    elif row['item'] == 'TEE':
        return 'EQU_TEE'
    else:
        return row['item']

def set_fit_size(row,fitting):
    if row[f'size_{fitting}'] == 'corridor_size':
        size = row['corridor_size']
        
    elif row[f'size_{fitting}'] == 'header_1_size':
        size = row['header_1_size']
        
    elif row[f'size_{fitting}'] == 'header_2_size':
        size = row['header_2_size']
        
    elif row[f'size_{fitting}'] == 'branch_size':
        size = row['branch_size']
        
    elif row[f'size_{fitting}'] == 'branch_1_size':
        size = row['branch_1_size']
        
    elif row[f'size_{fitting}'] == 'branch_2_size':
        size = row['branch_2_size']
        
    elif row[f'size_{fitting}'] == 'branch_3_size':
        size = row['branch_3_size']
        
    elif row[f'size_{fitting}'] == 'branch_4_size':
        size = row['branch_4_size']
    
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
            size = row[f'size_{fitting}']
        else:
            size = None
    
    if isinstance(size, (int, float)):
        fit_size_ceiled = max(size, row[f'size_{fitting}_ceil'])
        size = min(size, row[f'size_{fitting}_floor'])
    
    if row[f'material_{fitting}'] == 'steel':
        size = pipe_sizes_df.loc[pipe_sizes_df['pe_size'] == size, 'steel_size'].iloc[0]
    
    return size

def set_fit_class(row,fitting):
    if row[f'class_{fitting}'] == 'corridor_class':
        fit_class = row['corridor_class']
        
    elif row[f'class_{fitting}'] == 'header_1_class':
        fit_class = row['header_1_class']
        
    elif row[f'class_{fitting}'] == 'header_2_class':
        fit_class = row['header_2_class']
        
    elif row[f'class_{fitting}'] == 'branch_class':
        fit_class = row['branch_class']
        
    elif row[f'class_{fitting}'] == 'branch_1_class':
        fit_class = row['branch_1_class']
        
    elif row[f'class_{fitting}'] == 'branch_2_class':
        fit_class = row['branch_2_class']
        
    elif row[f'class_{fitting}'] == 'branch_3_class':
        fit_class = row['branch_3_class']
        
    elif row[f'class_{fitting}'] == 'branch_4_class':
        fit_class = row['branch_4_class']
        
    elif row[f'class_{fitting}'] == 'mode_class':
        possible_cols = [
            'corridor_class', 'header_1_class', 'header_2_class',
            'branch_class', 'branch_1_class', 'branch_2_class',
            'branch_3_class', 'branch_4_class'
        ]
        existing_cols = [col for col in possible_cols if col in row]
        values = [row[col] for col in existing_cols]
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
            fit_class = None
    
    if isinstance(fit_class, (int, float)):
        fit_class_ceiled = max(fit_class, row[f'class_{fitting}_ceil'])
        fit_class = min(fit_class_ceiled, row[f'class_{fitting}_floor'])

    try:
        if row[f'material_{fitting}'] == 'ansi_steel':
            fit_class = pipe_classes_df.loc[pipe_classes_df['sdr'] == fit_class, 'ansi_class'].iloc[0]
        elif row[f'material_{fitting}'] == 'as2129_steel':
            fit_class = pipe_classes_df.loc[pipe_classes_df['sdr'] == fit_class, 'as2129_class'].iloc[0]
    except:
        pass
    
    return fit_class

def filter_rows(row):
    if (row['type_ref'] == 'CON_RED' or row['type_ref'] == 'ECC_RED') and (row['fitting_size_1'] <= row['fitting_size_2']):
        return 'FILTER'
    elif (row['type_ref'] == 'TRANSITION') and (row['fitting_class_1'] >= row['fitting_class_2']):
        return 'FILTER'
    else:
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