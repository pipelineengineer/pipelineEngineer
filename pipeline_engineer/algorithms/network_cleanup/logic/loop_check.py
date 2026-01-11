import processing

def loop_checker(layer,loop_field):
    loops = processing.run("native:extractbyexpression", 
                            {'INPUT':layer,
                            'EXPRESSION':f'"{loop_field}" IS NOT NULL',
                            'OUTPUT':'memory:'})['OUTPUT']
    
    dissolved = processing.run("native:dissolve", 
                               {'INPUT':loops,
                                'FIELD':[],
                                'SEPARATE_DISJOINT':False,
                                'OUTPUT':'memory:'})['OUTPUT']
    
    split_with_lines = processing.run("native:splitwithlines", 
                                      {'INPUT':dissolved,
                                       'LINES':dissolved,
                                       'OUTPUT':'memory:'})['OUTPUT']
    
    return split_with_lines
