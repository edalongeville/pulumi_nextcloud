"""
Create an IAM user with the correct permissions
"""

import pulumi
import json
from pulumi_aws import iam

from storage import bucket

env = pulumi.get_stack()

# Create a policy with r/w permissions to our data bucket
jsonPolicy = bucket.arn.apply(
    lambda arn: json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetBucketLocation",
                        "s3:ListAllMyBuckets"
                    ],
                    "Resource": "arn:aws:s3:::*"
                },
                {
                    "Effect": "Allow",
                    "Action": "s3:*",
                    "Resource": [
                        f"{arn}",
                        f"{arn}/*"
                    ]
                }
            ]
        }
    )
)


policy = iam.Policy(
    f"nextcloud-policy-{env}",
    policy=jsonPolicy
)

# Create a user
user = iam.User(
    f"nextcloud-S3-user-{env}",
    name=f"nextcloud-s3-user-{env}"
)

userAccessKey = iam.AccessKey(
    f"nextcloud-user-access-key-{env}",
    user=user.id
)

# Attach the policy to the user
iam.PolicyAttachment(
    f"nextcloud-policy-attachment-{env}",
    policy_arn=policy.arn,
    users=[user.id])
