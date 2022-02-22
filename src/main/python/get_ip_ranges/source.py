"""
Copyright (c) 2020 VMware, Inc.

This product is licensed to you under the Apache License, Version 2.0 (the "License").
You may not use this product except in compliance with the License.

This product may include a number of subcomponents with separate copyright notices
and license terms. Your use of these subcomponents is subject to the terms and
conditions of the subcomponent's license, as noted in the LICENSE file.
"""

import requests
from vra_ipam_utils.ipam import IPAM
import logging
from urllib.parse import parse_qs
from vra_solidserver_utils.auth import SOLIDserverAuth
import vra_solidserver_utils as utils

def handler(context, inputs):

    ipam = IPAM(context, inputs)
    IPAM.do_get_ip_ranges = do_get_ip_ranges

    return ipam.get_ip_ranges()

def do_get_ip_ranges(self, auth_credentials, cert):

    username = auth_credentials["privateKeyId"]
    password = auth_credentials["privateKey"]
    auth = SOLIDserverAuth(username, password)

    properties = utils.get_properties(self.inputs)

    service = "/rest/ip_pool_list"
    url = "https://" + self.inputs["endpoint"]["endpointProperties"]["hostName"] + service

    site_name = properties.get('site_name')
    params = {}
    if site_name:
        params = {"WHERE": "site_name='{}'".format(site_name)}

    response = requests.get(url, params=params, auth=auth, verify=cert)

    result_ranges = []

    for pool in response.json():

        subnet_class_parameters = parse_qs(pool['subnet_class_parameters'])

        # startIPAddress     = utils.long2ip(int(pool["start_ip_addr"], 16))
        # endIPAddress       = utils.long2ip(int(pool["end_ip_addr"], 16))
        startIPAddress     = utils.hex2ip(pool["start_ip_addr"])
        endIPAddress       = utils.hex2ip(pool["end_ip_addr"])
        subnetPrefixLength = utils.subnet_size2prefix_length(pool["subnet_size"])
        gatewayAddress     = subnet_class_parameters.get('gateway', [None])[0]
        dnsSearchDomains   = subnet_class_parameters.get('domain_list', [None])[0].split(";")
        domain             = subnet_class_parameters.get('domain', [None])[0]
        dnsServerAddresses = properties.get('dnsServerAddresses', "").replace(" ", "").replace(",", ";").split(";")

        vlan = subnet_class_parameters.get("vlmvlan_vlan_id", ["Not set"])[0]

        description = "VLAN ID: {}".format(vlan)

        logging.debug('Found pool {}'.format(pool["pool_name"]))

        range = {
            "id"                : pool["pool_id"],      # String, Required
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

    logging.info('Found {} IP ranges'.format(len(result_ranges)))

    result = {
        "ipRanges": result_ranges
    }

    return result
