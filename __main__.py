import pulumi
import pulumi_aws as aws

size = "t2.micro"
# Before running this script, you MUST manually create a keypair
keyName = "AWS_EC2"  # PROVIDE YOUR OWN KEY PAIR NAME
availabilityZone = "eu-west-3b"  # PROVIDE YOUR OWN AZ
# Todo: Allow DB password to use special chars
mysqlRootPassword = "testeur56"  # Generate YOUR OWN password: https://passwordsgenerator.net/
mysqlNextcloudPassword = "testeur56"  # Generate YOUR OWN password: https://passwordsgenerator.net/

#region S3


# Create an AWS resource (S3 Bucket)
# Todo: Make S3 SSE work with Nextcloud
bucket = aws.s3.Bucket('nextcloud-bucket')
# Block all public access https://docs.aws.amazon.com/AmazonS3/latest/dev/access-control-block-public-access.html
aws.s3.BucketPublicAccessBlock('nextcloud-bucket-public-block',
                               bucket=bucket.id,
                               block_public_acls=True,
                               ignore_public_acls=True,
                               block_public_policy=True,
                               restrict_public_buckets=True)

# Export the name of the bucket
pulumi.export('bucket_name', bucket.id)
pulumi.export('bucket_arn', bucket.arn)
#endregion

#region Access

# Create a policy
jsonPolicy = pulumi.Output.concat("{\n\
    \"Version\": \"2012-10-17\",\n\
    \"Statement\": [\n\
        {\n\
            \"Effect\": \"Allow\",\n\
            \"Action\": [\n\
                \"s3:GetBucketLocation\",\n\
                \"s3:ListAllMyBuckets\"\n\
            ],\n\
            \"Resource\": \"arn:aws:s3:::*\"\n\
        },\n\
        {\n\
            \"Effect\": \"Allow\",\n\
            \"Action\": \"s3:*\",\n\
            \"Resource\": [\n\
                \"", bucket.arn, "\",\n\
                \"", bucket.arn, "/*\"\n\
            ]\n\
        }\n\
    ]\n\
}")
print(jsonPolicy)

policy = aws.iam.Policy('nextcloud-policy', policy=jsonPolicy)

# Create a user
user = aws.iam.User('nextcloud-S3-user', name='nextcloud-s3-user')
userAccessKey = aws.iam.AccessKey('user-access-key', user=user.id)

# Attach the policy to the user
aws.iam.PolicyAttachment('nextcloud-policy-attachment', policy_arn=policy.arn, users=[user.id])
#endregion

#region EC2

with open('userData.sh', 'r') as file:
    userScript = file.read()

userScript = userScript.replace('<MYSQL_NEXTCLOUD_PASSWORD>', mysqlNextcloudPassword)
userScript = userScript.replace('<MYSQL_ROOT_PASSWORD>', mysqlRootPassword)

userScript_final = pulumi.Output.all(bucket.id, userAccessKey.id, userAccessKey.secret).apply(
    lambda l:
        userScript.replace('<BUCKET_NAME>', l[0]).replace('<USER_KEY>', l[1]).replace('<USER_SECRET>', l[2])
)


# Retrieve the most recent Ubuntu Server 18.04 LTS (HVM), SSD Volume Type
ami = aws.get_ami(most_recent=True,
                  owners=["099720109477"],
                  filters=[{"name": "name", "values": ["ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*"]}])

# Create a Security Group allowing ssh access
group = aws.ec2.SecurityGroup('nextcloud-secgrp',
                              description='Enable SSH and HTTP/S access',
                              ingress=[
                                  {'protocol': 'tcp', 'from_port': 22, 'to_port': 22, 'cidr_blocks': ['0.0.0.0/0']},
                                  {'protocol': 'tcp', 'from_port': 443, 'to_port': 443, 'cidr_blocks': ['0.0.0.0/0']},
                                  {'protocol': 'tcp', 'from_port': 80, 'to_port': 80, 'cidr_blocks': ['0.0.0.0/0']}
                              ],
                              egress=[
                                  {'protocol': '-1', 'from_port': 0, 'to_port': 0, 'cidr_blocks': ['0.0.0.0/0']}
                              ])

# Create an EC2 (using the ami previously retrieved)
server = aws.ec2.Instance('webserver-www',
                          instance_type=size,
                          security_groups=[group.name],  # reference security group from above
                          ami=ami.id,
                          key_name=keyName,
                          associate_public_ip_address=True,
                          availability_zone=availabilityZone,
                          user_data=userScript_final)
elasticIp = aws.ec2.Eip('elastic-ip', instance=server.id)

# Exporting values to pulumi
pulumi.export('elasticIP', elasticIp.public_ip)
#endregion