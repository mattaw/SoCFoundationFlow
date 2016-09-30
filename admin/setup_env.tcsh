#!/bin/tcsh
set called=($_)
if ("$called" == "") then
	if ($?SFF_ADMIN) then
		set rootdir=$SFF_ADMIN
	else
		echo "Please set SFF_ADMIN to the repo admin folder."
		exit 1
	endif
else
	set rootdir=`dirname $called[2]`
	set rootdir=`cd $rootdir && pwd`
endif

set -f path=("$rootdir/veripool" $path:q)
set -f path=("$rootdir/waf/waf-current" $path:q)

setenv WAFDIR $rootdir/waf/waf-current

