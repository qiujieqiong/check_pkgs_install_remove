#!/bin/bash

apt-get update
apt install python3-pip
pip3 install --trusted-host pypi.douban.com -i http://pypi.douban.com/simple/ pandas
cd /check_pkgs_install_remove/docker_check
python3 get_sourcelist.py
mv /etc/apt/sources.list /etc/apt/sources.list.bak
mv base.list /etc/apt/sources.list.d/
mv rpa.list /etc/apt/sources.list.d/
mv upstream.list /etc/apt/sources.list.d/
apt-get -y update
python3 docker_check_apps.py
cat pkgs.info