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
from vra_solidserver_utils import SOLIDserverSession

def handler(context, inputs):

    ipam = IPAM(context, inputs)
    IPAM.do_deallocate_ip = do_deallocate_ip

    return ipam.deallocate_ip()

def do_deallocate_ip(self, auth_credentials, cert):

    hostname = self.inputs["endpoint"]["endpointProperties"]["hostName"]
    username = auth_credentials["privateKeyId"]
    password = auth_credentials["privateKey"]
    global session
    session = SOLIDserverSession(hostname, username, password, cert)

    deallocation_result = []
    for deallocation in self.inputs["ipDeallocations"]:
        deallocation_result.append(deallocate(self.inputs["resourceInfo"], deallocation))

    assert len(deallocation_result) > 0
    return {
        "ipDeallocations": deallocation_result
    }

def deallocate(resource, deallocation):
    ip_range_id = deallocation["ipRangeId"]
    site_id = ip_range_id.split("/")[0]
    ipAddress = deallocation["ipAddress"]

    logging.info(f"Deallocating IP address {ipAddress} from site {site_id}")

    service = "/rest/ip_delete"
    params = {
        "site_id" : site_id,
        "hostaddr" : ipAddress
    }
    response = session.request("DELETE", service, params=params)

    return {
        "ipDeallocationId": deallocation["id"],
        "message": response.text
    }
