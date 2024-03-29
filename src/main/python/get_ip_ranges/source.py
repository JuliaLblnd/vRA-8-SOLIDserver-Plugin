"""
Copyright (c) 2020 VMware, Inc.

This product is licensed to you under the Apache License, Version 2.0 (the "License").
You may not use this product except in compliance with the License.

This product may include a number of subcomponents with separate copyright notices
and license terms. Your use of these subcomponents is subject to the terms and
conditions of the subcomponent's license, as noted in the LICENSE file.

Implementation for EfficientIP SOLIDServer by Julia Leblond (JuliaLblnd)
"""

from vra_ipam_utils.ipam import IPAM
import logging
from vra_solidserver_utils import SOLIDserverSession
from vra_solidserver_utils import utils

def handler(context, inputs):

    ipam = IPAM(context, inputs)
    IPAM.do_get_ip_ranges = do_get_ip_ranges

    return ipam.get_ip_ranges()

def do_get_ip_ranges(self, auth_credentials, cert):

    hostname = self.inputs["endpoint"]["endpointProperties"]["hostName"]
    username = auth_credentials["privateKeyId"]
    password = auth_credentials["privateKey"]
    session = SOLIDserverSession(hostname, username, password, cert)

    global properties
    properties = utils.get_properties(self.inputs)
    use_pool   = properties.get('use_pool').lower() == "true"
    use_subnet = properties.get('use_subnet').lower() == "true"
    pool_site_name = properties.get('pool_site_name', '')
    subnet_site_name = properties.get('subnet_site_name', '')

    result_ranges = []

    if use_pool:
        service = "/rest/ip_pool_list"
        params = {}
        if pool_site_name:
            params = {"WHERE": "site_name='{}'".format(pool_site_name)}

        response = session.request("GET", service, params=params)
        pools = response.json()
        ranges_from_pools = convert_pools_or_subnets(pools)

        result_ranges.extend(ranges_from_pools)
        logging.info(f"Found {len(ranges_from_pools)} IP ranges from pools")

    if use_subnet:
        service = "/rest/ip_block_subnet_list"
        params = {}
        if subnet_site_name:
            params = {"WHERE": "site_name='{}' and is_terminal='1'".format(subnet_site_name)}

        response = session.request("GET", service, params=params)
        subnets = response.json()
        ranges_from_subnets = convert_pools_or_subnets(subnets)

        result_ranges.extend(ranges_from_subnets)
        logging.info(f"Found {len(ranges_from_subnets)} IP ranges from subnets")

    result = {
        "ipRanges": result_ranges
    }

    return result


def convert_pools_or_subnets(pools_or_subnets):
    result_ranges = []

    for element in pools_or_subnets:
        class_parameters = utils.parse_class_parameters(element['subnet_class_parameters'])
        subnetPrefixLength = utils.subnet_size2prefix_length(element["subnet_size"])

        # if key pool_name is present, it is a pool
        if "pool_name" in element:
            rangeId = "site:{}/subnet:{}/pool:{}".format(element["site_id"], element["subnet_id"], element["pool_id"])
            name = element["pool_name"]
            subnetStart = utils.hex2ip(element["subnet_start_ip_addr"])
            description = "Pool from subnet {}/{} ({})".format(subnetStart, subnetPrefixLength, element['subnet_name'])
            logging.info(f"Found pool {element['pool_name']} with ID {element['pool_id']}")

        # else, it is a block_subnet
        else:
            rangeId = "site:{}/subnet:{}".format(element["site_id"], element["subnet_id"])
            name = element["subnet_name"]
            description = "Subnet {}/{}, VLAN {} ({})".format(subnetStart, subnetPrefixLength, element["vlmvlan_vlan_id"], element["vlmvlan_name"])
            logging.info(f"Found subnet {element['subnet_name']} with ID {element['subnet_id']}")


        domain             = class_parameters.get('domain', [None])[0]
        startIPAddress     = utils.hex2ip(element["start_ip_addr"])
        endIPAddress       = utils.hex2ip(element["end_ip_addr"])
        gatewayAddress     = class_parameters.get('gateway', [None])[0]
        dnsSearchDomains   = class_parameters.get('domain_list', [""])[0].split(";")
        dnsServerAddresses = utils.parse_list(properties.get('dnsServerAddresses', ""))
        tags               = utils.parse_tags(class_parameters.get('vra_tags', [""])[0])

        range = {
            "id"                : rangeId,              # String, Required
            "name"              : name,                 # String, Required
            "description"       : description,          # String, Optional
            "startIPAddress"    : startIPAddress,       # String, Required
            "endIPAddress"      : endIPAddress,         # String, Required
            "ipVersion"         : "IPv4",               # Enum: {IPv4, IPv6}, Required
            "addressSpaceId"    : "",                   # String, Optional
            "gatewayAddress"    : gatewayAddress,       # String, Optional
            "subnetPrefixLength": subnetPrefixLength,   # Integer, Required
            "dnsServerAddresses": dnsServerAddresses,   # List<String>, Optional
            "domain"            : domain,               # String, Optional
            "dnsSearchDomains"  : dnsSearchDomains,     # List<String>, Optional
            "properties"        : {},                   # Map<String,String>
            "tags"              : tags                  # List<Tag>
        }

        result_ranges.append(range)

    return result_ranges
