"""
Provisions the EC2 instance running Nextcloud
"""
import pulumi
from pulumi_aws import get_ami, ec2

from storage import bucket
from access import userAccessKey
from security import mysqlNextcloudPassword, mysqlRootPassword

env = pulumi.get_stack()
config = pulumi.Config("nextcloud")
size = config.require("size")
keyPairName = config.require("keyPairName")
availabilityZone = config.require("availabilityZone")

# We first need to generate the userData script by filling the fields in userData.sh
with open('userData.sh', 'r') as file:
    userScript = file.read()

userScript_final = pulumi.Output.all(bucket.id,
                                     userAccessKey.id,
                                     userAccessKey.secret,
                                     mysqlNextcloudPassword.result,
                                     mysqlRootPassword.result
                                     ).apply(
    lambda l:
    userScript.replace('<BUCKET_NAME>', l[0])
    .replace('<USER_KEY>', l[1])
    .replace('<USER_SECRET>', l[2])
    .replace('<MYSQL_NEXTCLOUD_PASSWORD>', l[3])
    .replace('<MYSQL_ROOT_PASSWORD>', l[4])
)


# Retrieve the most recent Ubuntu Server 18.04 LTS (HVM), SSD Volume Type
ami = get_ami(
    most_recent=True,
    owners=["099720109477"],
    filters=[{"name": "name", "values": [
        "ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*"]}]
)

# Create a Security Group allowing ssh access
group = ec2.SecurityGroup(
    f"nextcloud-secgrp-{env}",
    description='Enable SSH and HTTP/S access',
    ingress=[
        {'protocol': 'tcp', 'from_port': 22,
            'to_port': 22, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': 'tcp', 'from_port': 443,
         'to_port': 443, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': 'tcp', 'from_port': 80,
         'to_port': 80, 'cidr_blocks': ['0.0.0.0/0']}
    ],
    egress=[
        {'protocol': '-1', 'from_port': 0,
         'to_port': 0, 'cidr_blocks': ['0.0.0.0/0']}
    ]
)

# Create an EC2 (using the ami previously retrieved)
server = ec2.Instance(
    f"nextcloud-webserver-www-{env}",
    instance_type=size,
    # reference security group from above
    security_groups=[group.name],
    ami=ami.id,
    key_name=keyPairName,
    associate_public_ip_address=True,
    availability_zone=availabilityZone,
    user_data=userScript_final,
    tags={'Name': f"nextcloud-{env}"}
)

elasticIp = ec2.Eip(
    f"nextcloud-elastic-ip-{env}",
    instance=server.id
)

# Exporting values to pulumi
pulumi.export('elasticIP', elasticIp.public_ip)
# endregion
