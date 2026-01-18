from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsEditorWidgetSetup
from qgis.PyQt.QtCore import Qt, QVariant

def create_additional_fitting_layer(pipeline_feature_layer):

    def setup_value_relation(layer,field_name,filter_exp,pipeline_feature_layer):
            widget = QgsEditorWidgetSetup(
                "ValueRelation", {
                    'Layer': pipeline_feature_layer.id(),
                    'Key': field_name,
                    'Value': field_name,
                    'FilterExpression': filter_exp, 
                    'AllowNull': False,
                    'OrderByValue': True,
                    'AllowMulti': False
                }
            )
            layer.setEditorWidgetSetup(layer.fields().indexOf(field_name), widget)
            
    def create_layer(geom_type,crs,name):
        return QgsVectorLayer(f"{geom_type}?crs={crs}",name,"memory")

    def add_fields(layer, field_list):
        provider = layer.dataProvider()
        provider.addAttributes(field_list)
        layer.updateFields()
    
    project_crs = QgsProject.instance().crs()
    
    layer = create_layer(geom_type='noGeometry',crs=project_crs.authid(),name='Additional Fittings List')
    
    add_fields(layer, 
                    [
                        QgsField("feat_id", QVariant.String),
                        QgsField("service", QVariant.String),
                        QgsField("assembly", QVariant.String),
                        QgsField("category", QVariant.String),
                        QgsField("type_ref", QVariant.String),
                        QgsField("fitting_size_1", QVariant.Double),
                        QgsField("fitting_size_2", QVariant.Double),
                        QgsField("fitting_class_1", QVariant.String),
                        QgsField("fitting_class_2", QVariant.String)
                    ]
               )
    
    field_name = 'assembly'
    filter_exp = '"feat_id" = current_value(\'feat_id\')'
    
    setup_value_relation(layer=layer,field_name=field_name,filter_exp=filter_exp,pipeline_feature_layer=pipeline_feature_layer)
    
    setup_value_relation(layer=layer,field_name='feat_id',filter_exp='',pipeline_feature_layer=pipeline_feature_layer)
    
    setup_value_relation(layer=layer,field_name='service',filter_exp=filter_exp,pipeline_feature_layer=pipeline_feature_layer)
    
    return layer