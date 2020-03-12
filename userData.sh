#!/bin/bash
apt update
apt install apache2 mysql-server -y
apt install php zip libapache2-mod-php php-gd php-json php-mysql php-curl php-mbstring php-intl php-imagick php-xml php-zip php-mysql -y

## MYSQL
#mysql_secure_installation
mysql --user="root" --execute="CREATE DATABASE nextcloud;
                                CREATE USER 'nextcloud'@'localhost' IDENTIFIED BY '<MYSQL_PASSWORD>';
                                GRANT ALL PRIVILEGES ON nextcloud.* TO 'nextcloud'@'localhost';
                                FLUSH PRIVILEGES;"

## Nextcloud Install
wget https://download.nextcloud.com/server/releases/latest-18.zip
unzip latest*.zip
mv nextcloud /var/www/html/
chown -R www-data:www-data /var/www/html/nextcloud

## Apache
APACHE_CONFIG=$(cat <<'EOF'
Alias /nextcloud '/var/www/html/nextcloud/'
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
);
echo "$APACHE_CONFIG" > /etc/apache2/sites-available/nextcloud.conf

# Apache conf
a2ensite nextcloud
a2enmod rewrite headers env dir mime
sed -i '/^memory_limit =/s/=.*/= 512M/' /etc/php/7.2/apache2/php.ini
systemctl restart apache2

# Connect to S3 (https://autoize.com/s3-compatible-storage-for-nextcloud/)
NEXTCLOUDS3CONFIG =$(cat <<'EOF'
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
            'region' => 'eu-west-3',   
    ),
),
];
EOF
);

echo $NEXTCLOUDS3CONFIG > /var/www/html/nextcloud/config/storage.config.php
chown -R www-data:www-data /var/www/html/nextcloud/config/storage.config.php
