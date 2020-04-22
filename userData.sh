#!/bin/bash

## Mount EBS Volume
# Make file system if necessary (only when the volume is new)
OUTPUT="$(file -s /dev/xvdh)"
if [[ $OUTPUT == *"/dev/xvdh: data"* ]]; then
  mkfs -t xfs /dev/xvdh
  NEWINSTALL=true
else
  NEWINSTALL=false
fi

# Create mount point
mkdir /mnt/ebs

# Get UUID and create fstab entry
REGEX="\/dev\/xvdh: UUID=\"(.+?)\" "
OUTPUT="$(blkid)"
if [[ $OUTPUT =~ $REGEX ]]; then
  echo "UUID=${BASH_REMATCH[1]}  /mnt/ebs  xfs  defaults,nofail  0  2" >> /etc/fstab
else
  echo "Could not find EBS UUID" >> /var/log/userData.log
  exit 1
fi

## Mount EBS tmp
# Make file system if necessary (only when the volume is new)
OUTPUT="$(file -s /dev/xvdi)"
if [[ $OUTPUT == *"/dev/xvdi: data"* ]]; then
  mkfs -t xfs /dev/xvdi
fi

# Create mount point
mkdir /mnt/temp

# Get UUID and create fstab entry
REGEX="\/dev\/xvdi: UUID=\"(.+?)\" "
OUTPUT="$(blkid)"
if [[ $OUTPUT =~ $REGEX ]]; then
  echo "UUID=${BASH_REMATCH[1]}  /mnt/temp  xfs  defaults,nofail  0  2" >> /etc/fstab
else
  echo "Could not find TMP EBS UUID" >> /var/log/userData.log
  exit 1
fi

# Mount
mount -a

# Install Mysql
apt update
apt install apache2 mysql-server -y

## MYSQL on EBS
# https://www.digitalocean.com/community/tutorials/how-to-move-a-mysql-data-directory-to-a-new-location-on-ubuntu-18-04
# Stop mysql
systemctl stop mysql
# Move Mysql data dir to EBS Volume (only on new install)
if [ "$NEWINSTALL" == true ]; then
  rsync -av /var/lib/mysql /mnt/ebs
fi
# Backup the current mysql data dir
mv /var/lib/mysql /var/lib/mysql.bak
# Configure mysql to use ebs as data dir
sed -i -e '/datadir/s/\/var\/lib\/mysql/\/mnt\/ebs\/mysql/' /etc/mysql/mysql.conf.d/mysqld.cnf
# Configure AppArmor to allow access
echo "alias /var/lib/mysql/ -> /mnt/ebs/mysql/," >> /etc/apparmor.d/tunables/alias
systemctl restart apparmor
# Recreate default dir to trick mysql into starting
sudo mkdir /var/lib/mysql/mysql -p
# Start mysql
systemctl start mysql

# Install other required packages
apt install php zip libapache2-mod-php php-gd php-json php-mysql php-curl php-mbstring php-intl php-imagick php-xml php-zip php-mysql software-properties-common -y
add-apt-repository universe -y
add-apt-repository ppa:certbot/certbot -y
apt install certbot python-certbot-apache -y
# Stop Apache during install
systemctl stop apache2

## MYSQL
# Todo: mysql_secure_installation
if [ "$NEWINSTALL" == true ]; then
  mysql --user="root" --execute="CREATE DATABASE nextcloud;
                                CREATE USER 'nextcloud'@'localhost' IDENTIFIED BY '<MYSQL_NEXTCLOUD_PASSWORD>';
                                GRANT ALL PRIVILEGES ON nextcloud.* TO 'nextcloud'@'localhost';
                                FLUSH PRIVILEGES;"
fi


## Nextcloud Install on EBS
if [ "$NEWINSTALL" == true ]; then
  wget https://download.nextcloud.com/server/releases/latest-18.zip
  unzip latest*.zip
  mv nextcloud /mnt/ebs/
  chown -R www-data:www-data /mnt/ebs/nextcloud
fi
ln -s /mnt/ebs/nextcloud /var/www/html/nextcloud

## Apache
APACHE_CONFIG=$(
  cat <<'EOF'
Alias / '/var/www/html/nextcloud/'
<Directory /var/www/html/nextcloud/>
    Options +FollowSymlinks
    AllowOverride All
      <IfModule mod_dav.c>
        Dav off
      </IfModule>
     
     SetEnv HOME /var/www/html/nextcloud
    SetEnv HTTP_HOME /var/www/html/nextcloud
</Directory>
EOF
)
echo "$APACHE_CONFIG" >/etc/apache2/sites-available/nextcloud.conf

# Apache conf
a2ensite nextcloud
a2enmod rewrite headers env dir mime socache_shmcb ssl
sed -i '/^memory_limit =/s/=.*/= 512M/' /etc/php/7.2/apache2/php.ini
echo "sys_temp_dir = \"/mnt/temp\"" >> /etc/php/7.2/apache2/php.ini
# systemctl restart apache2

# Connect to S3 (https://autoize.com/s3-compatible-storage-for-nextcloud/)
NEXTCLOUDS3CONFIG=$(
  cat <<'EOF'
<?php
$CONFIG = [
  'objectstore' => array(
    'class' => 'OC\\Files\\ObjectStore\\S3',
    'arguments' => array(
            'bucket' => '<BUCKET_NAME>',
            'key'    => '<USER_KEY>',
            'secret' => '<USER_SECRET>',
            'autocreate' => false,
            'use_ssl' => true,
            'use_path_style'=>false,   
            'region' => '<AWS_REGION>',   
    ),
),
];
EOF
)

echo "$NEXTCLOUDS3CONFIG" > /var/www/html/nextcloud/config/storage.config.php
chown -R www-data:www-data /var/www/html/nextcloud/config/storage.config.php

# Start Apache once conf done
systemctl start apache2