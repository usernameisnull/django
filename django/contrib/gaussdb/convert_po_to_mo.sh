#!/bin/bash

# 设置根目录
locale_dir="/root/python/projects/django/django/contrib/gaussdb/locale"

# 遍历locale目录下的每个子目录
for lang_dir in "$locale_dir"/*; do
  if [ -d "$lang_dir/LC_MESSAGES" ]; then
    po_file="$lang_dir/LC_MESSAGES/django.po"
    mo_file="$lang_dir/LC_MESSAGES/django.mo"

    # 检查.po文件是否存在
    if [ -f "$po_file" ]; then
      echo "Processing $po_file"
      # 执行msgfmt命令
      msgfmt "$po_file" -o "$mo_file"
    else
      echo "No django.po found in $lang_dir/LC_MESSAGES"
    fi
  fi
done
