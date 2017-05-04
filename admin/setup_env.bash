#!/bin/bash

if [ -z $SFF_ADMIN ]; then
  rootdir="${BASH_SOURCE[0]}";
  if ([ -h "${rootdir}" ]) then
    while([ -h "${rootdir}" ]) do rootdir=`readlink "${rootdir}"`; done
  fi
  pushd . > /dev/null
  cd `dirname ${rootdir}` > /dev/null
  rootdir=`pwd`;
  popd  > /dev/null
else
  rootdir=$SFF_ADMIN
fi

export PATH=$PATH:$rootdir/waf/waf-current
export WAFDIR=$rootdir/waf/waf-current


