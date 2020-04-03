# pulumi_nextcloud
Simply deploy Nextcloud to AWS using Pulumi

## What this does
This projects deploys a fully operation Nextcloud instance to AWS, using pulumi.

## Requirements
- An AWS account (with registered credit card)
- An AWS user with admin permissions (seriously, don't use the root account... and enable MFA!)
- A pulumi account
- If you're new to Pulumi, follow the instructions at https://www.pulumi.com/docs/get-started/aws/

## Pre deployment tasks
### Create an EC2 keypair:
https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#having-ec2-create-your-key-pair


## Deploy nextcloud
- Clone this repo
- In Pulumi.nextcloud-prod.yaml, fill the region closest to you
- In Pulumi.nextcloud-prod.yaml, chose your instance size (t2.micro is included in AWS free tier)
- In Pulumi.nextcloud-prod.yaml, put your keypair name (from pre deployment tasks)
- # TODO: Create pulumi stack
- # TODO: Create/activate the venv, install requirements
- In your terminal, navigate to this repo and type ```pulumi up```

## Post deployment tasks
Please note the stack outputs displayed in your terminal at the end of the install. They will be needed for the next steps.

Go to `http://<YOUR_ELASTIC_IP>`.

- Chose your admin account name (please avoid naming it "admin").
- Chose a secure password (You can use this generator: https://www.lastpass.com/password-generator )
- Data Folder: No change required here (should be "/var/www/html/nextcloud/data")

Fill the DB information:
- user: "nextcloud"
- password: see <mysql_nextcloud_passwd> from the stack outputs
- name: "nextcloud"
- host: "localhost"

Chose wether you want the recommended apps.
Press "Finish setup"

You may create accounts for your users, and start using nextcloud:
https://docs.nextcloud.com/

## Optional steps
### Increase performance
If you chose a t2.micro, or other small instance, you may want to disable the "Photos" app.
Logged in as admin, go to Apps (top right corner),  Active Apps, and disable "Photos".

### Let's encrypt!
**A domain name is required for this step.**

First, create a DNS A record pointing to your elasticIP. For instance, for cloud.mydomain.com, we create:

```cloud IN A <YOUR_ELASTIC_IP>```

Then, access your server via ssh (the keyPair you created before running the tool will be required):

```ssh ubuntu@<YOUR_ELASTIC_IP> -i <YOUR_KEYPAIR_FILE_NAME>.pem```

Once on the server, run Certbot:

```sudo certbot --apache```

Provide your email, your domain (cloud.mydomain.fr) and chose Redirect. Certbot will take care of everything.

Backup the certs:

```zip -r /home/ubuntu/letsencrypt.zip /etc/letsencrypt```

And from your local machine (NOT ON THE SERVER):

```scp -i <YOUR_KEYPAIR_FILE_NAME>.pem ubuntu@<YOUR_ELASTIC_IP>:/home/ubuntu/letsencrypt.zip .```

