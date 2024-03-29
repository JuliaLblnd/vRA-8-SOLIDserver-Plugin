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
from vra_solidserver_utils import parse_class_parameters

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

    if int(allocation["size"]) != 1:
        raise Exception("Allocating more than one address is not implemented")

    range_id_parts = range_id.split("/")
    site_id   = range_id_parts[0].split(":", 1)[1]
    subnet_id = range_id_parts[1].split(":", 1)[1]
    is_pool   = "/pool:" in range_id

    # Get domain of subnet
    service = "/rest/ip_block_subnet_info"
    params = {
        "subnet_id": subnet_id
    }
    response = session.request("GET", service, params=params)
    subnet = response.json()[0]
    class_parameters = parse_class_parameters(subnet['subnet_class_parameters'])
    domain = class_parameters.get('domain', [None])[0]

    # Get 1 free ip in pool or subnet
    service = "/rpc/ip_find_free_address"
    params = {
        "max_find" : 42
    }
    if is_pool:
        params["pool_id"] = range_id_parts[2].split(":", 1)[1]
    else:
        params["subnet_id"] = subnet_id

    if "start" in allocation.keys():
        params["begin_addr"] = allocation["start"]

    free_ip_response = session.request("OPTIONS", service, params=params)

    if free_ip_response.status_code == 204:
        logging.error("Range is full or do not exist in IPAM")
        logging.error(free_ip_response.text)
        raise Exception("Range is full or do not exist in IPAM")

    free_ips = free_ip_response.json()

    if len(free_ips) < 1 or int(free_ips[0]['errno']) != 0 :
        logging.error("Error retrieving free IP addresses in range")
        logging.error(free_ip_response.text)
        raise Exception("Error retrieving free IP addresses in range")

    hostaddr = free_ips[0]['hostaddr']

    result = {
        "ipAllocationId": allocation["id"],
        "ipRangeId"     : range_id,
        "ipVersion"     : "IPv4",
        "ipAddresses"   : None,
        "__ip_id"     : None
    }

    for free_ip in free_ips:
        hostaddr = free_ip['hostaddr']

        # Allocate IP
        service = "/rest/ip_add"
        params = {
            "add_flag" : "new_only",
            "site_id"  : site_id,
            "name"     : resource["name"] + ("." + domain if domain else ""),
            "hostaddr" : hostaddr
        }
        response = session.request("POST", service, params=params)

        if response.status_code == 201:
            # 201 Created
            # [{"ret_oid":"6910"}]
            ip_id = response.json()[0]["ret_oid"]
            logging.info(f"Allocated IP address {hostaddr} (ip_id: {ip_id}) to {resource['name']} in subnet {subnet_id}")
            logging.info(response.text)
            result["ipAddresses"] = [hostaddr]
            result["__ip_id"] = ip_id
            break

    if result["ipAddresses"] == None or result["__ip_id"] == None:
        logging.error(f"Failed to allocate IP address in range {range_id}")
        raise Exception("Failed to allocate IP address")

    return result

## Rollback any previously allocated addresses in case this allocation request contains multiple ones and failed in the middle
def rollback(allocation_result):
    for allocation in reversed(allocation_result):
        logging.info(f"Rolling back allocation {str(allocation)}")
        ipAddresses = allocation.get("ipAddresses", None)

        service = "/rest/ip_delete"
        for ipAddress in ipAddresses:
            params = {
                "ip_id" : allocation["__ip_id"]
            }
            response = session.request("DELETE", service, params=params)

    return
