
def extract_xyz(line_layer,dem_layer,chainage,layer_id_field):
    chainage_in_deg = chainage / 111111
    
    #generating points
    points = processing.run("native:pointsalonglines", 
                                        {'INPUT':layer,
                                         'DISTANCE':chainage_in_deg,
                                         'START_OFFSET':0,
                                         'END_OFFSET':0,
                                         'OUTPUT':'memory:'})['OUTPUT']

    #converting from degrees to metres (rough)
    chainage =  processing.run("native:fieldcalculator", 
                                        {'INPUT':points,
                                         'FIELD_NAME':'chainage',
                                         'FIELD_TYPE':1,
                                         'FIELD_LENGTH':0,
                                         'FIELD_PRECISION':0,
                                         'FORMULA':'"distance" * 111111',
                                         'OUTPUT':'memory:'})['OUTPUT']

    #adding xy data
    xy_added = processing.run("qgis:exportaddgeometrycolumns", 
                                        {'INPUT':chainage,
                                         'CALC_METHOD':0,
                                         'OUTPUT':'memory:'})['OUTPUT']

    #sampling elevations
    sampled =  processing.run("native:rastersampling", 
                                        {'INPUT':xy_added,
                                         'RASTERCOPY':dem_layer,
                                         'COLUMN_PREFIX':'elev_m',
                                         'OUTPUT':'memory:'})['OUTPUT']

    #dropping distance (degrees) and angle
    xyz_layer = processing.run("native:retainfields", 
                                        {'INPUT':sampled,
                                         'FIELDS':[layer_id_field,'chainage','x_coord','y_coord','elev_m1'],
                                         'OUTPUT':'memory:'})['OUTPUT']

    return xyz_layer