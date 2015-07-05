#!/bin/bash
MYSQL_ENERGY_USER=energy
MYSQL_ENERGY_PASSWORD=password

MYSQL_ROOT_PASSWORD=password
MYSQL_HOST=10.10.10.51


function mysql_cmd() {
    set +o xtrace
    mysql -uroot -p$MYSQL_ROOT_PASSWORD -h$MYSQL_HOST -e "$@"
    set -o xtrace
}



# for rebuild the databases
function create_database() {
    cnt=`mysql_cmd "show databases;" | grep energy | wc -l`
    if [[ $cnt -gt 0 ]]; then
        mysql_cmd "DROP DATABASE energy;"
    fi

    # add % to root for  remote request
    mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'; FLUSH PRIVILEGES;"
    mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD'  WITH GRANT OPTION; FLUSH PRIVILEGES;"

    # create user
    cnt=`mysql_cmd "select * from mysql.user;" | grep $MYSQL_ENERGY_USER | wc -l`
    if [[ $cnt -eq 0 ]]; then
        mysql_cmd "create user '$MYSQL_ENERGY_USER'@'%' identified by '$MYSQL_ENERGY_PASSWORD';"
        mysql_cmd "flush privileges;"
    fi

    # create database
    cnt=`mysql_cmd "show databases;" | grep energy | wc -l`
    if [[ $cnt -eq 0 ]]; then
        mysql_cmd "create database energy CHARACTER SET utf8;"
        mysql_cmd "grant all privileges on energy.* to '$MYSQL_ENERGY_USER'@'%' identified by '$MYSQL_ENERGY_PASSWORD';"
        mysql_cmd "grant all privileges on energy.* to 'root'@'%' identified by '$MYSQL_ROOT_PASSWORD';"
        mysql_cmd "flush privileges;"
    fi
}
