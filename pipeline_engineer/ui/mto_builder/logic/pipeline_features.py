import processing

from .pipeline_feature_functions.bends import *
from .pipeline_feature_functions.tee_junctions import *
from .pipeline_feature_functions.four_way_unions import *
from .pipeline_feature_functions.attach_pipe_attributes import *
from .pipeline_feature_functions.pipe_summariser import *
from .pipeline_feature_functions.point_summariser import *

def summarise_feature_layers(point_layer, line_layer, line_id_field, service_description, 
                             service, id_expression, assembly_expression,include_tees_bends_unions,min_bend_angle):

    #id_expression = repr(id_expression)
    #assembly_expression = repr(assembly_expression)

    bends = summarise_bends(layer=line_layer,id_field=line_id_field,min_bend_angle=min_bend_angle,feature_id_exp="CONCAT('BEND_',LPAD($id,5,'00000'))")

    tees = summarise_tees(layer=line_layer,id_field=line_id_field,id_expression="CONCAT('JUNCTION_',LPAD($id,5,'00000'))")

    unions = summarise_four_way_unions(layer=line_layer,id_field=line_id_field,id_expression="CONCAT('UNION_',LPAD($id,5,'00000'))")
    
    layer_summaries = []

    if include_tees_bends_unions:

        if bends.featureCount() != 0:
            bends_summary =             bends_summary = summarise_points(point_layer=bends,
                                           point_id_formula='"feat_id"',
                                           join_to_line_layer=True,
                                           line_layer=line_layer,line_id_field=line_id_field,
                                           fields_to_retain=[],
                                           service=service,
                                           assembly_formula='CASE\r\nWHEN "angle" <=15 THEN \'11_BEND\'\r\nWHEN "angle" <=25 THEN \'22_BEND\'\r\nWHEN "angle" <=35 THEN \'30_BEND\'\r\nWHEN "angle" <=50 THEN \'45_BEND\'\r\nWHEN "angle" <=65 THEN \'60_BEND\'\r\nWHEN "angle" <=95 THEN \'90_BEND\'\r\nELSE NULL\r\nEND')

            bends_summary.setName('Bend Summary')

            layer_summaries.append(bends_summary)

        if tees.featureCount() != 0:
            
            tee_summary = summarise_points(point_layer=tees,
                                           point_id_formula='"feat_id"',
                                           join_to_line_layer=False,
                                           line_layer=line_layer,line_id_field=line_id_field,
                                           fields_to_retain=['branch','header_1','header_2'],
                                           service=service,
                                           assembly_formula="'JCT'")
      
            tee_summary.setName('Tee Summary')

            layer_summaries.append(tee_summary)

        if unions.featureCount() != 0:
            unions_summary = summarise_points(point_layer=unions,
                                              point_id_formula='"feat_id"',
                                              join_to_line_layer=False,
                                              line_layer=line_layer,line_id_field=line_id_field,
                                              fields_to_retain=['branch_1','branch_2','branch_3','branch_4'],
                                              service=service,
                                              assembly_formula="'UNION'")

            unions_summary.setName('Union Summary')

            layer_summaries.append(unions_summary)
    
    point_summary = summarise_points(point_layer=point_layer,
                                     point_id_formula=id_expression,
                                     join_to_line_layer=True,
                                     line_layer=line_layer,
                                     line_id_field=line_id_field,
                                     fields_to_retain=[],
                                     service=service,
                                     assembly_formula=assembly_expression) 

    point_summary.setName('Points Summary')

    layer_summaries.append(point_summary)
    
    merged_points = processing.run("native:mergevectorlayers", 
                                    {'LAYERS':layer_summaries,
                                     'CRS':None,
                                     'OUTPUT':'memory:'})['OUTPUT']

    return merged_points