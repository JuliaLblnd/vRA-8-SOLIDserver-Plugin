# Changelog

## v0.9.1 - 2023-10-13

 - Improve IP Allocation rollback by using `ip_id` instead of `site_id`
 - Removing the import of `Request` (importing `SOLIDserverSession` is enough)
 - Improving imports of module `vra_solidserver_utils`

## v0.9.0 - 2023-09-24

 - Use flag `new_only` to avoid allocating the same address on concurrent requests
 - Improve of Allocate IP operation
 - Added more exception details
 - Corrected the HTTP verb in Allocate IP operation
 - Improving the IP Range description
 - Only retrieve terminal subnets 

## v0.8.0 - 2023-07-07

 - New feature: Implemented the `start` parameter in Allocate IP operation, so an IP can be specified to be allocated

## v0.7.1 - 2023-05-24

 - No change in code, clean rebuild.

## v0.7.0 - 2023-05-22

 - Code refactoring
 - Changed `provider.name` to remove space considered as an invalid character since vRealize Automation 8.?
 - **Warning:** Change of `provider.name` in these release, cause the package to be recognized as a new one and not as a new version of the previous.
	You will need to reassign networks to ranges if upgrading from a previous version (older than v0.7.0).

## v0.6.1 - 2023-02-17

 - Rebuild of v6.0 with `provider.name` corrected as in v0.7.0
 - No code change

## v0.6 - 2022-06-29

 - New feature: Get tags from IPAM custom subnet_class_parameters `vra_tags`

## v0.5 - 2022-03-07

 - Update Python Request from 2.21.0 to 2.25.1

## v0.4 - 2022-03-03
