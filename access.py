"""
Create an IAM user with the correct permissions
"""

import pulumi
from pulumi_aws import iam

from storage import bucket

env = pulumi.get_stack()

# Create a policy with r/w permissions to our data bucket
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

policy = iam.Policy(
    'nextcloud-policy', 
    policy=jsonPolicy
    )

# Create a user
user = iam.User(
    'nextcloud-S3-user', 
    name=f"nextcloud-s3-user-{env}"
    )

userAccessKey = iam.AccessKey(
    'user-access-key', 
    user=user.id
    )

# Attach the policy to the user
iam.PolicyAttachment(
    'nextcloud-policy-attachment', 
    policy_arn=policy.arn, 
    users=[user.id])
