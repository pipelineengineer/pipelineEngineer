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

def disjoint_check(layer,selected_features):
        if selected_features:
            pass
        else:
            processing.run("qgis:randomselection", 
                                    {'INPUT':layer,
                                     'METHOD':0,
                                     'NUMBER':1})

        previous_selection_count = len(layer.selectedFeatureIds())
        new_selection_count = -1  # Initialize to start the loop

        # Loop until no more features are selected by location
        while new_selection_count != previous_selection_count:
            previous_selection_count = len(layer.selectedFeatureIds())
            
            # Run the select by location algorithm
            processing.run("native:selectbylocation", {
                'INPUT': layer, 
                'PREDICATE': [4],  # "4" corresponds to "touches" in the select by location tool
                'INTERSECT': QgsProcessingFeatureSourceDefinition(layer.id(), True), 
                'METHOD': 1  # Add to current selection
            })
            
            # Update new selection count
            new_selection_count = len(layer.selectedFeatureIds())

        # The loop stops when no more features are added to the selection
        print(f"Selection complete. Total selected features: {new_selection_count}")