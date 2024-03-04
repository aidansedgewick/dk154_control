import json

# Load the JSON file
with open('dfosc_setup.json') as file:
    data = json.load(file)

print(data['positions']['grism']['G3'])
