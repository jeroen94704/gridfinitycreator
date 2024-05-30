import os

def get_size_help():
    with open(os.path.dirname(__file__) + '/help_files/size_help.html', 'r') as reader:
        return reader.read()
    
def get_magnet_help():
    with open(os.path.dirname(__file__) + '/help_files/magnet_help.html', 'r') as reader:
        return reader.read()
    
def get_stackinglip_help():
    with open(os.path.dirname(__file__) + '/help_files/stackinglip_help.html', 'r') as reader:
        return reader.read()
    
def get_labeltab_help():
    with open(os.path.dirname(__file__) + '/help_files/labeltab_help.html', 'r') as reader:
        return reader.read()
    
def get_exportformat_help():
    with open(os.path.dirname(__file__) + '/help_files/export_format_help.html', 'r') as reader:
        return reader.read()
    
def get_scoopramp_help():
    with open(os.path.dirname(__file__) + '/help_files/scoopramp_help.html', 'r') as reader:
        return reader.read()
    
def get_compartment_help():
    with open(os.path.dirname(__file__) + '/help_files/compartment_help.html', 'r') as reader:
        return reader.read()