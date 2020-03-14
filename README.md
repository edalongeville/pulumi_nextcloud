# pulumi_nextcloud
Simply deploy Nextcloud to AWS using Pulumi

## What this does

## Requirements

## Pre install tasks

##Post install
### Configure your instance
Go to `http://<YOUR_ELASTIC_IP>`.

Create an admin account (please use a secure password, and avoid naming it "admin").

Fill the DB information:
- user: nextcloud
- password: see "mysqlPassword" in "\_\_main\_\_.py"
- name: nextcloud
- host: localhost

Press "Finish setup"


### Let's encrypt! (optional)
**A domain name is required for this step.**

First, create a DNS A record pointing to your elasticIP. For instance, for cloud.mydomain.com, we create:

```cloud IN A <YOUR_ELASTIC_IP>```

Then, access to your server through ssh (the keyPair you created before running the tool will be required):

```ssh ubuntu@<YOUR_ELASTIC_IP> -i <YOUR_KEYPAIR_FILE_NAME>.pem```

Once on the server, run Certbot:

```sudo certbot --apache```

Provide your email, your domain (cloud.mydomain.fr) and chose Redirect. Certbot will take care of everything.

Backup the certs:

```zip -r /home/ubuntu/letsencrypt.zip /etc/letsencrypt```

And from your local machine (NOT ON THE SERVER):

```scp -i <YOUR_KEYPAIR_FILE_NAME>.pem ubuntu@<YOUR_ELASTIC_IP>:/home/ubuntu/letsencrypt.zip .```

