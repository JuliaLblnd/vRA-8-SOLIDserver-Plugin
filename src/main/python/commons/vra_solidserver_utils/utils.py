"""
vra_solidserver_utils.utils
~~~~~~~~~~~~~~~~

"""

import json
from socket import inet_ntoa, inet_aton
from struct import pack, unpack

def long2ip(longip):
    if longip <= 4294967295 and longip >=0:
        return inet_ntoa(pack("!L", longip))
    else:
        return False

def ip2long(ip):
    return unpack("!L", inet_aton(ip))[0]

def hex2ip(hex_ip):
    return "{}.{}.{}.{}".format(
        int(hex_ip[0] + hex_ip[1], 16),
        int(hex_ip[2] + hex_ip[3], 16),
        int(hex_ip[4] + hex_ip[5], 16),
        int(hex_ip[6] + hex_ip[7], 16)
    )

def ip2hex(ip):
    ip_bytes = ip.split(".")
    return "{}{}{}{}".format(
        "{:02x}".format(int(ip_bytes[0])),
        "{:02x}".format(int(ip_bytes[1])),
        "{:02x}".format(int(ip_bytes[2])),
        "{:02x}".format(int(ip_bytes[3]))
    )

def subnet_size2prefix_length(subnet_size):
    subnet_size = int(subnet_size)
    prefix_length = 32
    while subnet_size > 1:
        prefix_length = prefix_length - 1
        subnet_size = subnet_size // 2
    return str(prefix_length)

def get_properties(inputs):
    inputs = inputs.get("endpoint", inputs)
    properties_list = inputs["endpointProperties"].get("properties", [])
    properties_list = json.loads(properties_list)
    properties = {}
    for prop in properties_list:
        properties[prop["prop_key"]] = prop["prop_value"]

    return properties

def build_params(filters):
    where = ""
    where_list = []
    for filter in filters:
        if not where:
            where = where + filter + ""

        where = where + " and "

    params = {"WHERE": where}
