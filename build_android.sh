#!/bin/bash

adb=~/Android/sdk/platform-tools/adb
bid=studio.almann.pyzza

#echo "Available devices:"
#$adb shell getprop ro.product.nickname ro.product.cpu.abi
#echo

flet build apk

printf "Removing previous version: "
$adb uninstall $bid

#printf "Clearing cached data: "
#$adb shell pm clear $bid

$adb install build/apk/Pyzza.apk
$adb shell am start -n $bid/$bid.MainActivity
