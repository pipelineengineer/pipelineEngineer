import os

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal

import pandas as pd
import numpy as np

from qgis.core import (QgsVectorLayer,QgsField,QgsFields,QgsFeature,QgsGeometry,QgsPointXY,QgsProject)
from qgis.core import (
    QgsSymbol,
    QgsRendererRange,
    QgsGraduatedSymbolRenderer,
    QgsProject,
    QgsWkbTypes,
    QgsUnitTypes
)
from PyQt5.QtCore import QVariant
from qgis.core import QgsEditorWidgetSetup, QgsProject
from qgis.core import QgsProcessingFeatureSourceDefinition, QgsProject, QgsFeatureRequest, QgsVectorLayer, QgsMapLayerProxyModel, QgsMapLayer
from PyQt5.QtGui import QColor
import processing

from qgis.core import (
    QgsVectorLayer,
    QgsGraduatedSymbolRenderer,
    QgsRendererRange,
    QgsSymbol,
    QgsProject
)

#helper functions
def field_to_string(layer,field): #converts a field in a layer into a string
    layer_2 = layer
    #ensuring the layer is selected
    processing.run("native:selectbylocation",   
                                            {'INPUT':layer_2,
                                             'PREDICATE':[3], #equals
                                             'INTERSECT':layer_2,
                                             'METHOD':0}) #create new selection
    layer_selected = layer.selectedFeatures()
    layer_list = [f[field] for f in layer_selected]
    list_as_string = ','.join(map(str,layer_list))
    return list_as_string

def field_to_list(layer,field): #converts a field in a layer into a list
    layer_2 = layer
    processing.run("native:selectbylocation",   
                                            {'INPUT':layer_2,
                                             'PREDICATE':[3], #equals
                                             'INTERSECT':layer_2,
                                             'METHOD':0}) #create new selection
    layer_selected = layer.selectedFeatures()
    layer_list = [f[field] for f in layer_selected]
    return layer_list

def field_to_list_non_selected(layer,field): #converts a field in a layer into a list
    layer_list = [f[field] for f in layer]
    return layer_list


def load_layer(layer,layer_name): #loads layer by set name to session
    layer.setName(layer_name)
    QgsProject.instance().addMapLayer(layer)

def layer_to_df(layer):
        cols = [f.name() for f in layer.fields()]
        data = ([f[col] for col in cols] for f in layer.getFeatures())
        df = pd.DataFrame.from_records(data=data, columns = cols)
        return df

def load_layer_graduated(layer,layer_name,graduate_field): #loads layer by set name to session
        """
        Applies a 4-class graduated style to a layer based on the given field.
        Adds the styled layer to the QGIS project.
        """

        # Check if the classification field exists
        if graduate_field not in [field.name() for field in layer.fields()]:
            raise ValueError(f"Field '{graduate_field}' not found in the layer.")

        # Extract values from layer (you must have this helper implemented)
        layer_df = layer_to_df(layer)
        values = layer_df[graduate_field].dropna().tolist()

        if not values:
            raise ValueError(f"No data in field '{graduate_field}' to classify.")

        min_val = min(values)
        max_val = max(values)

        # Avoid division by zero
        if max_val == min_val:
            raise ValueError(f"Field '{graduate_field}' has constant value: {min_val}")

        # Calculate class breaks
        step = (max_val - min_val) / 4
        breaks = [min_val + step * i for i in range(5)]

        # Define colors for 4 ranges
        hex_colors = ["#307bff", "#7552aa", "#ba2955", "#ff0000"]
        ranges = []

        for i in range(4):
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.setColor(QColor(hex_colors[i]))

            # ⬇️ Set line weight if layer is a line geometry
            if QgsWkbTypes.geometryType(layer.wkbType()) == QgsWkbTypes.LineGeometry:
                symbol_layer = symbol.symbolLayer(0)
                symbol_layer.setWidth(0.5)
                symbol_layer.setWidthUnit(QgsUnitTypes.RenderMillimeters)

            label = f"{breaks[i]:.2f} - {breaks[i+1]:.2f}"
            rng = QgsRendererRange(breaks[i], breaks[i+1], symbol, label)
            ranges.append(rng)

        # Apply graduated renderer
        renderer = QgsGraduatedSymbolRenderer(graduate_field, ranges)
        renderer.setMode(QgsGraduatedSymbolRenderer.Custom)
        layer.setRenderer(renderer)

        # Set layer name and add to project
        layer.setName(layer_name)
        QgsProject.instance().addMapLayer(layer)

def sample_raster_values(layer_name,dem_name):
     
    if type(layer_name) == QgsVectorLayer:
        layer = layer_name
    else:
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]

    raster_sample = processing.run("native:rastersampling", 
                                   {'INPUT':layer,
                                    'RASTERCOPY':dem_name,
                                    'COLUMN_PREFIX':'raster_val',
                                    'OUTPUT':'memory:'})['OUTPUT']

    return raster_sample

def xyz_data(layer,dem,chainage):
    distance = chainage * 0.000009
    
    #saving features from selected line layer
    selected = processing.run("native:saveselectedfeatures", 
                                        {'INPUT':layer,
                                         'OUTPUT':'memory:'})['OUTPUT']

    #dissolves them into one layer
    dissolved = processing.run("native:dissolve", 
                                        {'INPUT':selected,
                                         'FIELD':[],
                                         'SEPARATE_DISJOINT':False,
                                         'OUTPUT':'memory:'})['OUTPUT']

    #generates points along the dissolved layer
    points = processing.run("native:pointsalonglines", 
                                        {'INPUT':dissolved,
                                         'DISTANCE':distance,
                                         'START_OFFSET':0,
                                         'END_OFFSET':0,
                                         'OUTPUT':'memory:'})['OUTPUT']

    chainage_added = processing.run("native:fieldcalculator", 
                                                {'INPUT':points,
                                                 'FIELD_NAME':'chainage',
                                                 'FIELD_TYPE':0,
                                                 'FIELD_LENGTH':0,
                                                 'FIELD_PRECISION':0,
                                                 'FORMULA':'ROUND("distance" / 0.000009, 0)',
                                                 'OUTPUT':'memory:'})['OUTPUT']

    #samples elevation data from DEM layer
    sampled = processing.run("native:rastersampling", 
                                        {'INPUT':chainage_added,
                                         'RASTERCOPY':dem,
                                         'COLUMN_PREFIX':'elevation',
                                         'OUTPUT':'memory:'})['OUTPUT']

    #adds in crs (xcoord and ycoord)
    geom_added = processing.run("qgis:exportaddgeometrycolumns", 
                                        {'INPUT':sampled,
                                         'CALC_METHOD':0,
                                         'OUTPUT':'memory:'})['OUTPUT']

    #retains only necessary fields
    retained = processing.run("native:retainfields", 
                                        {'INPUT':geom_added,
                                         'FIELDS':['chainage','elevation1','xcoord','ycoord'],
                                         'OUTPUT':'memory:'})['OUTPUT']
    
    return retained

def setup_value_relation(layer,field_name,junction_layer):
            widget = QgsEditorWidgetSetup(
                "ValueRelation", {
                    'Layer': junction_layer.id(),
                    'Key': 'name',
                    'Value': 'name',
                    'AllowNull': False,
                    'OrderByValue': True,
                    'AllowMulti': False
                }
            )
            layer.setEditorWidgetSetup(layer.fields().indexOf(field_name), widget)

def create_layer_from_pandas_df(df):
    print(df.head())
    # Creation of my QgsVectorLayer with no geometry 
    temp = QgsVectorLayer("none","result","memory")
    temp_data = temp.dataProvider()
    # Start of the edition 
    temp.startEditing()

    # Creation of my fields 
    for head in df : 
        myField = QgsField( head, QVariant.Double)
        temp.addAttribute(myField)
    # Update     
    temp.updateFields()

    # Addition of features
    # [1] because i don't want the indexes 
    for row in df.itertuples():
        f = QgsFeature()
        f.setAttributes([row[1],row[2]])
        temp.addFeature(f)
        print(row)
    # saving changes and adding the layer
    temp.commitChanges()
    return temp

def connect_field_combo_box_to_layer(layer_combo_box,field_combo_box):
    layer_combo_box.layerChanged.connect(
         lambda layer, fc=field_combo_box: fc.setLayer(layer if layer and layer.type() == QgsMapLayer.VectorLayer else None)
         )

    # Immediately apply the logic using the current layer
    layer = layer_combo_box.currentLayer()
    if layer and layer.type() == QgsMapLayer.VectorLayer:
        field_combo_box.setLayer(layer)
    else:
        field_combo_box.setLayer(None)

def re_calc_graduated(layer, qml_path):
    layer.loadNamedStyle(qml_path)
    renderer = layer.renderer()

    if renderer.type() == 'graduatedSymbol':
        field_name = renderer.classAttribute()
        attr_index = layer.fields().indexOf(field_name)

        # Most builds (like yours) want both layer and field index
        try:
            renderer.updateClasses(layer, attr_index)
        except TypeError:
            # fallback for older versions that expect field name instead
            renderer.updateClasses(layer, field_name)

        # Reapply and refresh
        layer.setRenderer(renderer)
        layer.triggerRepaint()