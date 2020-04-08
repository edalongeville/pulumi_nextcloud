"""
Provisions the EC2 instance running Nextcloud
"""
import pulumi
from pulumi_aws import get_ami, ec2, ebs

from storage import bucket
from access import userAccessKey
from security import mysqlNextcloudPassword, mysqlRootPassword

env = pulumi.get_stack()
config = pulumi.Config("nextcloud")
size = config.require("size")
keyPairName = config.require("keyPairName")
availabilityZone = config.require("availabilityZone")

# We first need to know our Instance IP (required in userData)
elastic_ip = ec2.Eip(
    f"nextcloud-elastic-ip-{env}",
    # instance=instance.id
)

# We first need to generate the userData script by filling the fields in userData.sh
with open('userData.sh', 'r') as file:
    userScript = file.read()

userScript_final = pulumi.Output.all(bucket.id,
                                     userAccessKey.id,
                                     userAccessKey.secret,
                                     mysqlNextcloudPassword.result,
                                     mysqlRootPassword.result,
                                     elastic_ip.public_ip
                                     ).apply(
    lambda l:
    userScript.replace('<BUCKET_NAME>', l[0])
    .replace('<USER_KEY>', l[1])
    .replace('<USER_SECRET>', l[2])
    .replace('<MYSQL_NEXTCLOUD_PASSWORD>', l[3])
    .replace('<MYSQL_ROOT_PASSWORD>', l[4])
    .replace('<ELASTIC_IP>', l[5])
    .replace('<AWS_REGION>', pulumi.Config("aws").require("region"))
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
instance = ec2.Instance(
    f"nextcloud-webserver-www-{env}",
    instance_type=size,
    # reference security group from above
    security_groups=[group.name],
    ami=ami.id,
    key_name=keyPairName,
    associate_public_ip_address=True,
    # public_ip=elasticIp,
    availability_zone=availabilityZone,
    user_data=userScript_final,
    tags={'Name': f"nextcloud-{env}"}
)

# Associate our Elastic IP to the instance
elastic_ip_association = ec2.EipAssociation(
    f"nextcloud-elastic-ip-association{env}",
    opts=None,
    allocation_id=None,
    allow_reassociation=None,
    instance_id=instance.id,
    network_interface_id=None,
    private_ip_address=None,
    public_ip=elastic_ip.public_ip,
    __props__=None)


# Create a volume to store the DB
storage_volume = ebs.Volume(
    resource_name=f"nextcloud-ebs-{env}",
    size=1,
    availability_zone=availabilityZone,
    tags={'Name': f"nextcloud-storage-{env}"}
)

# Attach the volume to the EC2
ec2.VolumeAttachment(
    resource_name=f"nextcloud-ec2-volume-attachment-{env}",
    device_name="/dev/sdh",
    instance_id=instance.id,
    skip_destroy=True,
    volume_id=storage_volume.id,
)

# Exporting values to pulumi
pulumi.export('elasticIP', elastic_ip.public_ip)
pulumi.export('database_name', "nextcloud")
pulumi.export('database_user', "nextcloud")
