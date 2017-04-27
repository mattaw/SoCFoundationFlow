#!/bin/bash

tests=(defaults defaults_n_user basic_dependencies include_only  src_only  tb_include_only tb_only two_src find_src basic_views)

#Testing the check option
for ((i = 0; i < ${#tests[@]}; i++)); do
    printf "\nRunning: ${tests[$i]} \n"
    printf "waf configure --top_level=${tests[$i]} --check\n\n"
    eval "waf configure --top_level=${tests[$i]} --check"
    if [ $? -ne 0 ]; then exit 1; fi

done

#Testing without the check
for ((i = 0; i < ${#tests[@]}; i++)); do
    printf "\nRunning: ${tests[$i]} \n"
    printf "waf configure --top_level=${tests[$i]}\n"
    eval "waf configure --top_level=${tests[$i]}"
    if [ $? -ne 0 ]; then exit 1;  fi

done

