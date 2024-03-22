import json
from dfosc import controls

controller = controls()
# Load the JSON file
with open('dfosc_setup.json') as file:
    data = json.load(file)

#print(data['grism']['G7'])

controller.grism_init(data['grism']['G7'])