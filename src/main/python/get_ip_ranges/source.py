"""
Copyright (c) 2020 VMware, Inc.

This product is licensed to you under the Apache License, Version 2.0 (the "License").
You may not use this product except in compliance with the License.

This product may include a number of subcomponents with separate copyright notices
and license terms. Your use of these subcomponents is subject to the terms and
conditions of the subcomponent's license, as noted in the LICENSE file.

Implementation for EfficientIP SOLIDServer by Julia Leblond (JuliaLblnd)
"""

import requests
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

    properties = utils.get_properties(self.inputs)
    site_name = properties.get('site_name')

    service = "/rest/ip_pool_list"
    params = {}
    if site_name:
        params = {"WHERE": "site_name='{}'".format(site_name)}

    response = session.get(service, params=params)

    result_ranges = []

    for pool in response.json():

        class_parameters = utils.parse_class_parameters(pool['subnet_class_parameters'])

        domain             = class_parameters.get('domain', [None])[0]
        rangeId            = "site:{}/pool:{}/domain:{}".format(pool["site_id"], pool["pool_id"], domain)
        startIPAddress     = utils.hex2ip(pool["start_ip_addr"])
        endIPAddress       = utils.hex2ip(pool["end_ip_addr"])
        subnetPrefixLength = utils.subnet_size2prefix_length(pool["subnet_size"])
        gatewayAddress     = class_parameters.get('gateway', [None])[0]
        dnsSearchDomains   = class_parameters.get('domain_list', [None])[0].split(";")
        dnsServerAddresses = utils.parse_list(properties.get('dnsServerAddresses', ""))

        vlan = class_parameters.get("vlmvlan_vlan_id", ["Not set"])[0]
        description = "VLAN ID: {}".format(vlan)

        logging.info(f"Found pool {pool['pool_name']} with ID {pool['pool_id']}")

        range = {
            "id"                : rangeId,              # String, Required
            "name"              : pool["pool_name"],    # String, Required
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
            # "tags"              : tags                  # List<Tag>
        }

        logging.debug(range)
        result_ranges.append(range)

    logging.info(f"Found {len(result_ranges)} IP ranges")

    result = {
        "ipRanges": result_ranges
    }

    return result
