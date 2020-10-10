from box import Box
import yaml

settings = Box.from_yaml(filename="./Settings.yaml", Loader=yaml.FullLoader) 
