import os
import pandas as pd

from qgis.core import (QgsVectorLayer,QgsField,QgsFields,QgsFeature,QgsGeometry,QgsPointXY,QgsProject, QgsMapLayer)

def dataframes_to_csv(dataframes,file_names):

        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Define new folder name and path
        new_folder_name = 'working'
        new_folder_path = os.path.join(script_dir, new_folder_name)

        # Create the folder if it doesn't exist
        os.makedirs(new_folder_path, exist_ok=True)

        result_layers = []

        for i, dataframe in enumerate(dataframes):
                
            file_name = file_names[i]
            file_path = os.path.join(new_folder_path, f'{file_name}.csv')
            dataframe.to_csv(file_path,index=False)
        
            uri = f"file:///{file_path}?delimiter=,&detectTypes=yes&geomType=none"

            results_layer = QgsVectorLayer(uri, f'{file_name}','delimitedtext')
            
            results_layer.setName(file_name)
            
            result_layers.append(results_layer)

        return result_layers