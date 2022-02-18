"""
vra_solidserver_utils.utils
~~~~~~~~~~~~~~~~

"""

import json
from socket import inet_ntoa
from struct import pack

def long2ip(longip):
    if longip <= 4294967295 and longip >=0:
        return inet_ntoa(pack("!L", longip))
    else:
        return false

def subnet_size2prefix_length(subnet_size):
    subnet_size = int(subnet_size)
    prefix_length = 32
    while subnet_size > 1:
        prefix_length = prefix_length - 1
        subnet_size = subnet_size // 2
    return prefix_length

def get_properties(inputs):
    inputs = inputs.get("endpoint", inputs)
    properties_list = inputs["endpointProperties"].get("properties", [])
    properties_list = json.loads(properties_list)
    properties = {}
    for prop in properties_list:
        properties[prop["prop_key"]] = prop["prop_value"]

    return properties
