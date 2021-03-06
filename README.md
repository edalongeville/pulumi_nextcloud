# pulumi_nextcloud
Simply deploy Nextcloud to AWS using Pulumi

## What this does
This projects deploys a fully operational [Nextcloud](https://nextcloud.com/) instance to [AWS](https://aws.amazon.com/), using [Pulumi](https://www.pulumi.com/).

## Requirements
- An AWS account (with registered credit card)
- An AWS user with admin permissions (seriously, don't use the root account... and enable MFA!)
- A pulumi account
- If you're new to Pulumi, follow the [getting started instructions](https://www.pulumi.com/docs/get-started/aws/).

## Pre deployment tasks
### Create an EC2 keypair:
Follow this [AWS Documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#having-ec2-create-your-key-pair).

## Deploy nextcloud
- Clone this repo
- In Pulumi.prod.yaml, chose the region/AZ closest to you
- In Pulumi.prod.yaml, chose your instance size (t2.micro is included in AWS free tier)
- In Pulumi.prod.yaml, put your keypair name (from pre deployment tasks)
- `pulumi stack` => Create new stack =>name it "`prod`"
- `python3 -m venv venv; source venv/bin/activate; pip3 install -r requirements.txt`
- `pulumi up`
- It should take about 10 minutes for your instance to be ready. Be patient!

## Post deployment tasks
Please note the stack outputs displayed in your terminal at the end of the install. They will be needed for the next steps.

Go to `http://<YOUR_ELASTIC_IP>`.

- Chose your admin account name (please avoid naming it "admin").
- Chose a secure password (You can use this generator: https://www.lastpass.com/password-generator )
- Data Folder: No change required here (should be "/var/www/html/nextcloud/data")

Fill the DB information:
- user: "nextcloud"
- password: see `mysql_nextcloud_passwd` from the stack outputs
- name: "nextcloud"
- host: "localhost"

Chose wether you want the recommended apps.
Press "Finish setup"

You may now create accounts for your users, and start using nextcloud:
https://docs.nextcloud.com/

## Optional steps
### Increase performance
If you chose a t2.micro, or other small instance, you may want to disable the "Photos" app.
Logged in as admin, go to Apps (top right corner),  Active Apps, and disable "Photos".

### Let's encrypt!
**A domain name is required for this step.**

First, create a DNS A record pointing to your elasticIP. For instance, for cloud.mydomain.com, we create:

    cloud IN A <YOUR_ELASTIC_IP>

Then, access your server via ssh (the keyPair you created before running the tool will be required):

    ssh ubuntu@<YOUR_ELASTIC_IP> -i <YOUR_KEYPAIR_FILE_NAME>.pem

Once on the server, run Certbot:

    sudo certbot --apache

Provide your email, your domain (cloud.mydomain.fr) and chose Redirect. Certbot will take care of everything.

Open Apache config file:

    vim /var/www/html/nextcloud/config/config.php

Ensure the trusted_domains array contains your domain, and not an IP (replace if needed):

    'trusted_domains' =>
      array (
        0 => 'cloud.mydomain.fr',
      ),


Backup the certs:

    zip -r /mnt/ebs/letsencrypt.zip /etc/letsencrypt

## Troubleshooting
### My Nextcloud DB reached the max size!
The nextcloud Data and DB are stored on an EBS Volume. If your database reached the maximum size:
- In Pulumi.***STACK***.yaml, increase `nextcloud:volume_size_G`
- Update the stack with `pulumi up`
- ssh to your instance, and type as root: `xfs_growfs -d /mnt/ebs`
- You can verify the success with `df -h`

# Destroy the stack
Because your data is protected, you need to take some actions before destroying the stack:
- Backup all your data
- Empty the S3 bucket (from AWS Management console)
- Type `pulumi destroy`. You'll get an error message with a resource URN at the end.
- Type `pulumi state unprotect URN_FROM_PREVIOUS_STEP -y`
- Type `pulumi destroy`