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
    IPAM.do_allocate_ip = do_allocate_ip

    return ipam.allocate_ip()

def do_allocate_ip(self, auth_credentials, cert):

    hostname = self.inputs["endpoint"]["endpointProperties"]["hostName"]
    username = auth_credentials["privateKeyId"]
    password = auth_credentials["privateKey"]
    global session
    session = SOLIDserverSession(hostname, username, password, cert)

    allocation_result = []
    try:
        resource = self.inputs["resourceInfo"]
        for allocation in self.inputs["ipAllocations"]:
            allocation_result.append(allocate(resource, allocation, self.context, self.inputs["endpoint"]))
    except Exception as e:
        try:
            rollback(allocation_result)
        except Exception as rollback_e:
            logging.error(f"Error during rollback of allocation result {str(allocation_result)}")
            logging.error(rollback_e)
        raise e

    assert len(allocation_result) > 0
    return {
        "ipAllocations": allocation_result
    }

def allocate(resource, allocation, context, endpoint):

    last_error = None
    for range_id in allocation["ipRangeIds"]:

        logging.info(f"Allocating from range {range_id}")
        try:
            return allocate_in_range(range_id, resource, allocation, context, endpoint)
        except Exception as e:
            last_error = e
            logging.error(f"Failed to allocate from range {range_id}: {str(e)}")

    logging.error("No more ranges. Raising last error")
    raise last_error


def allocate_in_range(range_id, resource, allocation, context, endpoint):

    range_id_parts = range_id.split("/")
    site_id = range_id_parts[0]
    pool_id = range_id_parts[1]

    service = "/rpc/ip_find_free_address"
    params = {
        "max_find" : 1,
        "pool_id": pool_id
    }
    response = session.get(service, params=params)
    response_json = response.json()[0]
    hostaddr = response_json['hostaddr']

    service = "/rest/ip_add"
    params = {
        "site_id"  : site_id,
        "name"     : resource["name"] + '.renater.fr',
        "hostaddr" : hostaddr
    }
    response = session.request("POST", service, params=params)

    logging.info(f"Allocated IP address {hostaddr} to {resource['name']} in pool {pool_id}")
    logging.info(response.text)

    result = {
        "ipAllocationId": allocation["id"],
        "ipRangeId"     : range_id,
        "ipVersion"     : "IPv4",
        "ipAddresses"   : [hostaddr],
        "__site_id"     : site_id
    }

    return result

## Rollback any previously allocated addresses in case this allocation request contains multiple ones and failed in the middle
def rollback(allocation_result):
    for allocation in reversed(allocation_result):
        logging.info(f"Rolling back allocation {str(allocation)}")
        ipAddresses = allocation.get("ipAddresses", None)

        service = "/rest/ip_delete"
        params = {
            "site_id" : allocation["__site_id"]
        }
        for ipAddress in ipAddresses:
            params["hostaddr"] = ipAddress
            response = session.request("DELETE", service, params=params)

    return
