#!/bin/tcsh
set called=($_)
if ("$called" == "") then
	if ($?SOCET_ADMIN) then
		set rootdir=$SOCET_ADMIN
	else
		echo "Please set SOCET_ADMIN to the repo admin folder."
		exit 1
	endif
else
	set rootdir=`dirname $called[2]`
	set rootdir=`cd $rootdir && pwd`
endif

set -f path=("$rootdir/veripool" $path:q)
set -f path=("$rootdir/waf/waf-current" $path:q)

setenv WAFDIR $rootdir/waf/waf-current

