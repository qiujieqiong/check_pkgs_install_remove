#!/bin/bash -e

echo ${PWD}

docker pull hub.deepin.io/deepin-sid-64:latest

docker run --rm -t \
-v ${PWD}:/docker_check_pkgs_install_remove \
-e BASE=$BASE -e BASE_CODENAME=$BASE_CODENAME -e RPA=$RPA -e RPA_CODENAME=$RPA_CODENAME -e UPSTREAM=$UPSTREAM \
hub.deepin.io/deepin-sid-64 \
bash /docker_check_pkgs_install_remove/check_install_remove.sh
