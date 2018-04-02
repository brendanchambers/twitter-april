__author__ = 'Brendan'

import json

json_credentials_file = open('../local/credentials.json','r')
creds = json.load(json_credentials_file)

print creds['consumer_key']
