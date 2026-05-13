#!/bin/bash

version=1.0rc0

mkdir -p build/pyside
export PYTHONPATH=src/pyzza/pyside_app:src
#pyside6-deploy --config-file pysidedeploy.spec --keep-deployment-files

fpm -s dir -t deb \
    -n pyzza \
    -v $version \
    --force \
    --package build/pyside/ \
    --description "Pyzza is for pyzzas and more" \
    --maintainer "k.j.m.godin-dubois@vu.nl" \
    --url "https://github.com/kgd-al/pyzza" \
    --deb-no-default-config-files \
    --after-install scripts/post-install.deb.sh \
    build/pyside/pyzza.bin=/usr/local/bin/pyzza \
    assets/icon.png=/usr/share/icons/hicolor/512x512/apps/pyzza.png \
    pyzza.desktop=/usr/share/applications/pyzza.desktop
