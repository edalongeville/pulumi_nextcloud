import pulumi
import pulumi_aws as aws

config = pulumi.Config("nextcloud")
availabilityZone = config.require("availabilityZone")
region = pulumi.Config("aws").require("region")

if region in availabilityZone:
    import storage
    import access
    import security
    import instance
else:
    pulumi.log.error("Please chose an AZ from the defined Region")
