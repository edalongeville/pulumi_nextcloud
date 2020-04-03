"""
Create a Bucket to store our data
"""

import pulumi
from pulumi_aws import s3

env = pulumi.get_stack()

bucket = s3.Bucket(f"nextcloud-bucket-{env}")
# Block all public access https://docs.aws.amazon.com/AmazonS3/latest/dev/access-control-block-public-access.html
s3.BucketPublicAccessBlock(
    f"nextcloud-bucket-public-block-{env}",
    bucket=bucket.id,
    block_public_acls=True,
    ignore_public_acls=True,
    block_public_policy=True,
    restrict_public_buckets=True)

# Export the name of the bucket
pulumi.export('bucket_name', bucket.id)
pulumi.export('bucket_arn', bucket.arn)
