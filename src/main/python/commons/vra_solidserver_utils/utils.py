"""
vra_solidserver_utils.utils
~~~~~~~~~~~~~~~~

EfficientIP SOLIDserver utils for vRA

:copyright: (c) 2021 by Julia Leblond.
:license: CeCILL 2.1, see LICENSE for more details.
"""

from json import loads as json_loads
from urllib.parse import parse_qs

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
    properties_list = json_loads(properties_list)
    properties = {}
    for prop in properties_list:
        properties[prop["prop_key"]] = prop["prop_value"]

    return properties

def parse_list(strlist):
    return strlist.replace(" ", "").replace(",", ";").split(";")

def parse_class_parameters(class_parameters):
    return parse_qs(class_parameters)

def parse_tags(tags_str):
    if len(tags_str) < 1:
        return []
    tags_str_list = parse_list(tags_str)
    tags = []
    for tag_str in tags_str_list:
        new_tag = {}
        tag = tag_str.split(":")
        new_tag["key"] = tag[0]
        if len(tag) == 2:
            new_tag["value"] = tag[1]
        tags.append(new_tag)
    return tags
