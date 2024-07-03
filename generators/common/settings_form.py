import os

def get_standard_settings_form():
    with open(os.path.dirname(__file__) + '/settings_form.html', 'r') as reader:
        return reader.read()    