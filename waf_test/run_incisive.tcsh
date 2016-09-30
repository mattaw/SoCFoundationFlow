#!/bin/bash

tests=(defaults defaults_n_user basic_dependencies include_only  src_only  tb_include_only tb_only two_src find_src basic_views)

for ((i = 0; i < ${#tests[@]}; i++)); do
    printf "\nRunning: ${tests[$i]} \n"
    printf "waf configure --top_level=${tests[$i]} verify_source\n"
    eval "waf configure --top_level=${tests[$i]} verify_source"
    if [ $? -ne 0 ]; then exit 1;  fi

done
