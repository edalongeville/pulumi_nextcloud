"""
Generate the passwords we will use in the rest of the project
"""

import pulumi
from pulumi_random import RandomPassword

env = pulumi.get_stack()


mysqlRootPassword = RandomPassword(
    f"nextcloud-mysql-root-password-{env}",
    length=16,
    override_special="_%@",
    special=True
)

mysqlNextcloudPassword = RandomPassword(
    f"nextcloud-mysql-nextcloud-password-{env}",
    length=16,
    override_special="_%@",
    special=True
)


pulumi.export('mysql_root_passwd', mysqlRootPassword.result)
pulumi.export('mysql_nextcloud_passwd', mysqlNextcloudPassword.result)
