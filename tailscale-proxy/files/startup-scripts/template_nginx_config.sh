#!/bin/sh

for i in `find /etc/nginx/templates -type f -iname "*.tpl"`; do
  file=$(basename $i)
  echo "Templating $i"
  gomplate -f $i -o "/etc/nginx/conf.d/${file%.*}"
done
