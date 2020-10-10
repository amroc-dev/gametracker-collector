from box import Box
import yaml

settings = Box.from_yaml(filename="./_Settings.yaml", Loader=yaml.FullLoader) 
