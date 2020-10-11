from box import Box
import yaml

settings = Box.from_yaml(filename="./Settings.yaml", Loader=yaml.FullLoader) 

def hasTestArgs(argv):
    for arg in argv:
        if arg.lower() == "-test" or arg.lower() == "-t":
            return True

    return False
