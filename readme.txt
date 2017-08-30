1.请先执行bash run.sh来安装测试环境, 并在/etc/sudoers 的最后一行加上your_user_name  ALL=(ALL) NOPASSWD:ALL
2.然后执行python3 check_apps.py password，因为需要密码，所以请在执行脚本后面加上password
3.执行完毕后会生成result.html文件,这个文件可以看到所有app的执行命令，desktopfile的路径，安装，打开和删除状态
4.脚本运行完毕后，有的app会更改屏幕分辨率，比如rockdodger会更改为800*600，可能会有些许窗口没有关掉，请手动关掉，关不掉的请killall startdde
