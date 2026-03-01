import processing

def extract_merge_selected_features(layer_list,layer_name):
            
            selected_feature_layers = []
            
            for layer in layer_list:
                
                layer_selected_features = processing.run("native:saveselectedfeatures", {'INPUT':layer,'OUTPUT':'memory:'})['OUTPUT']
                
                layer_selected_features.setName(f'{layer.name()} Selected Features')
                
                selected_feature_layers.append(layer_selected_features)
                
            merged_layers =  processing.run("native:mergevectorlayers", {'LAYERS':selected_feature_layers,'CRS':None,'OUTPUT':'memory:'})['OUTPUT']
            
            merged_layers.setName(layer_name)
            
            return merged_layers