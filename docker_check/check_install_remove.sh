#!/bin/bash

apt-get update
apt-get -y install python3-pip dbus
LC_CTYPE="en_US.UTF-8" pip3 install --trusted-host pypi.douban.com -i http://pypi.douban.com/simple/ pandas
cd /docker_check_pkgs_install_remove/check_pkgs_install_remove/docker_check
#python3 get_sourcelist.py
#mv /etc/apt/sources.list /etc/apt/sources.list.bak
#mv base.list /etc/apt/sources.list.d/
#mv rpa.list /etc/apt/sources.list.d/
#mv upstream.list /etc/apt/sources.list.d/
apt-get -y update
env
export LANG=en_US.UTF-8
python3 docker_check_apps.py
cat pkgs.info