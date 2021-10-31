#!/bin/sh

for i in `find /etc/nginx/templates-tcpconf.d/ -type f -iname "*.tpl"`; do
  file=$(basename $i)
  echo "Templating $i"
  gomplate -f $i -o "/etc/nginx/tcpconf.d/${file%.*}"
done
