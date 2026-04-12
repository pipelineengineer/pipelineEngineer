import os
import sys
import pandas as pd
import numpy as np
import random

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsProcessingFeatureSourceDefinition, QgsProject, QgsFeatureRequest, QgsVectorLayer
from qgis.core import QgsMapLayerProxyModel
import processing

# Get the parent folder (one level up from the current script)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)  # Add it to sys.path

from .function_helpers import *

def recursive_selection_downstream(edges):

    selected_count = edges.selectedFeatureCount()

    if selected_count == 0:
        return

    selected_lines = processing.run("native:saveselectedfeatures", 
                                            {'INPUT':edges,
                                             'OUTPUT':'memory:'})['OUTPUT']

    lines_ided = processing.run("native:fieldcalculator", 
                                            {'INPUT':edges,
                                             'FIELD_NAME':'numeric_id',
                                             'FIELD_TYPE':1, # Integer
                                             'FIELD_LENGTH':0,
                                             'FIELD_PRECISION':0,
                                             'FORMULA':'$id',
                                             'OUTPUT':'memory:'})['OUTPUT']
    
    processing.run("native:selectbylocation", {'INPUT':lines_ided,'PREDICATE':[3],'INTERSECT':selected_lines,'METHOD':0})
    
    specific_vertices = processing.run("native:extractspecificvertices", 
                                        {'INPUT':lines_ided,
                                         'VERTICES':'0,-1',
                                         'OUTPUT':'memory:'})['OUTPUT']
    
    while True:
        # Creating list
        selected_lines = lines_ided.selectedFeatures()
        selected_lines_list = [f['numeric_id'] for f in selected_lines]
        selected_lines_string = ','.join(map(str,selected_lines_list))
        
        exp = f' "numeric_id" IN ({selected_lines_string}) AND "vertex_pos" = -1'
        
        processing.run("qgis:selectbyexpression", {'INPUT':specific_vertices,'EXPRESSION':exp,'METHOD':0})
        
        selected_vertices = processing.run("native:saveselectedfeatures", 
                                                {'INPUT':specific_vertices,
                                                 'OUTPUT':'memory:'})['OUTPUT']
        
        processing.run("native:selectbylocation", 
                                    {'INPUT':specific_vertices,
                                     'PREDICATE':[3], # Equals
                                     'INTERSECT':selected_vertices,
                                     'METHOD':0}) # Create new selection

        processing.run("qgis:selectbyexpression", 
                                    {'INPUT':specific_vertices,
                                     'EXPRESSION':f'"numeric_id" NOT IN ({selected_lines_string}) AND "vertex_pos" = 0',
                                     'METHOD':3})
        
        # Creating list
        selected_vertices = specific_vertices.selectedFeatures()
        selected_vertex_list = [f['numeric_id'] for f in selected_vertices]
        selected_vertex_string = ','.join(map(str,selected_vertex_list))
        
        if selected_vertex_list:
            vert_exp = f' "numeric_id" IN ({selected_vertex_string})'
            
            processing.run("qgis:selectbyexpression", 
                                        {'INPUT':lines_ided,
                                         'EXPRESSION':vert_exp,
                                         'METHOD':1}) #adding to current selection
        
        else:
            break
    
    directed_lines = processing.run("native:saveselectedfeatures", 
                                            {'INPUT':lines_ided,
                                             'OUTPUT':'memory:'})['OUTPUT']
    
    processing.run("native:selectbylocation", 
                                    {'INPUT':edges,
                                     'PREDICATE':[3], # Equals
                                     'INTERSECT':directed_lines,
                                     'METHOD':0}) # Create new selection