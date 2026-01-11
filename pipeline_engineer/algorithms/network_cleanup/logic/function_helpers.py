import os

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal

import pandas as pd
import numpy as np

from qgis.core import (QgsVectorLayer,QgsField,QgsFields,QgsFeature,QgsGeometry,
                       QgsPointXY,QgsProcessingFeatureSourceDefinition, 
                       QgsFeatureRequest, QgsMapLayerProxyModel,
                       QgsEditorWidgetSetup, QgsProject,QgsMapLayer)

from PyQt5.QtCore import QVariant
import processing

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

def connect_field_combo_box_to_layer(layer_combo_box,field_combo_box):
    layer_combo_box.layerChanged.connect(lambda layer, fc=field_combo_box: fc.setLayer(layer if layer and layer.type() == QgsMapLayer.VectorLayer else None))

    # Immediately apply the logic using the current layer
    layer = layer_combo_box.currentLayer()
    if layer and layer.type() == QgsMapLayer.VectorLayer:
        field_combo_box.setLayer(layer)
    else:
        field_combo_box.setLayer(None)

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

def load_layer(layer,layer_name): #loads layer by set name to session
    layer.setName(layer_name)
    QgsProject.instance().addMapLayer(layer)

def layer_to_df(layer):
        cols = [f.name() for f in layer.fields()]
        data = ([f[col] for col in cols] for f in layer.getFeatures())
        df = pd.DataFrame.from_records(data=data, columns = cols)
        return df

def xyz_data(layer,id_field,dem,chainage):
    distance = chainage * 0.000009

    #generates points along the dissolved layer
    points = processing.run("native:pointsalonglines", 
                                        {'INPUT':layer,
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
                                         'FIELDS':[id_field,'chainage','elevation1','xcoord','ycoord'],
                                         'OUTPUT':'memory:'})['OUTPUT']
    
    return retained
    
def line_costs(lines,dem_layer,internal_d_field):
    lines_ided = processing.run("native:fieldcalculator", 
                                        {'INPUT':lines,
                                         'FIELD_NAME':'line_id',
                                         'FIELD_TYPE':1,
                                         'FIELD_LENGTH':0,
                                         'FIELD_PRECISION':0,
                                         'FORMULA':'$id',
                                         'OUTPUT':'memory:'})['OUTPUT']

    line_starts = processing.run("native:extractspecificvertices", 
                                        {'INPUT':lines_ided,
                                         'VERTICES':'0',
                                         'OUTPUT':'memory:'})['OUTPUT']

    line_ends = processing.run("native:extractspecificvertices", 
                                        {'INPUT':lines_ided,
                                         'VERTICES':'-1',
                                         'OUTPUT':'memory:'})['OUTPUT']

    starts_sampled = processing.run("native:rastersampling", 
                                        {'INPUT':line_starts,
                                         'RASTERCOPY':dem_layer,
                                         'COLUMN_PREFIX':'inlet_elev',
                                         'OUTPUT':'memory:'})['OUTPUT']

    ends_sampled = processing.run("native:rastersampling", 
                                        {'INPUT':line_ends,
                                         'RASTERCOPY':dem_layer,
                                         'COLUMN_PREFIX':'outlet_elev',
                                         'OUTPUT':'memory:'})['OUTPUT']

    line_start_elev_added = processing.run("native:joinattributestable", 
                                        {'INPUT':lines_ided,
                                         'FIELD':'line_id',
                                         'INPUT_2':starts_sampled,
                                         'FIELD_2':'line_id',
                                         'FIELDS_TO_COPY':['inlet_elev1'],
                                         'METHOD':1,
                                         'DISCARD_NONMATCHING':False,
                                         'PREFIX':'',
                                         'OUTPUT':'memory:'})['OUTPUT']

    line_ends_elev_added = processing.run("native:joinattributestable", 
                                        {'INPUT':line_start_elev_added,
                                         'FIELD':'line_id',
                                         'INPUT_2':ends_sampled,
                                         'FIELD_2':'line_id',
                                         'FIELDS_TO_COPY':['outlet_elev1'],
                                         'METHOD':1,
                                         'DISCARD_NONMATCHING':False,
                                         'PREFIX':'',
                                         'OUTPUT':'memory:'})['OUTPUT']

    start_renamed = processing.run("native:renametablefield", 
                                        {'INPUT':line_ends_elev_added,
                                         'FIELD':'inlet_elev1',
                                         'NEW_NAME':'inlet_elev',
                                         'OUTPUT':'memory:'})['OUTPUT']

    end_renamed = processing.run("native:renametablefield", 
                                        {'INPUT':start_renamed,
                                         'FIELD':'outlet_elev1',
                                         'NEW_NAME':'outlet_elev',
                                         'OUTPUT':'memory:'})['OUTPUT']

    elevation_diff = processing.run("native:fieldcalculator", 
                                        {'INPUT':end_renamed,
                                         'FIELD_NAME':'elev_diff',
                                         'FIELD_TYPE':0,
                                         'FIELD_LENGTH':0,
                                         'FIELD_PRECISION':0,
                                         'FORMULA':'"inlet_elev" - "outlet_elev"',
                                         'OUTPUT':'memory:'})['OUTPUT']

    cost_calc = processing.run("native:fieldcalculator", 
                                        {'INPUT':elevation_diff,
                                         'FIELD_NAME':'cost',
                                         'FIELD_TYPE':0,
                                         'FIELD_LENGTH':0,
                                         'FIELD_PRECISION':0,
                                         'FORMULA':f'"elev_diff" + ($length / ("{internal_d_field}"^5))',
                                         'OUTPUT':'memory:'})['OUTPUT']

    return cost_calc