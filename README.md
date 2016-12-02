#SoC Foundation Flow

##Setting up the waf Build System

Add the following entries to your .cshrc or .tcshrc:
```
setenv SFF_ADMIN <path to the "admin" dir in the checked out git repository>
source $SFF_ADMIN/setup_env.tcsh
```

##Using the waf Build System
Please refer to the waf_test directory for a bunch of examples of code in units (a unit is a related set of verilog files).

Note the system supports the advanced concept of views to enable you to transparently change unit behaviour to support FPGA or SoC synthesis or simulation without having to copy or modify source files. This is an alpha feature.
