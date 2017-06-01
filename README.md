# SoCFoundationFlow (SFF)

## Setting up SFF

Bash:

Add the following lines to your ~/.bashrc file.
~~~~
export SFF_ADMIN=<absolute path to admin directory of SFF>
source $SFF_ADMIN/setup_env.bash
export SFF_SIM_ENV=<Simulation Environment>
~~~~

Tcsh:

Add the following lines to your ~/.cshrc file.
~~~~
setenv SFF_ADMIN <absolute path to admin directory of SFF>
source $SFF_ADMIN/setup_env.tcsh
setenv SFF_SIM_ENV <Simulation Environment>
~~~~

## Running WAF

All files created by WAF will end up in the build directory.

Clearing the build directory:
~~~
waf distclean
~~~

Setting up your project:
~~~
waf configure --top_level=<top_level>
~~~

Running a simulation without the gui:
~~~
waf verify_source
~~~

Running a simulation with the gui:
~~~
waf sim_source
~~~

Outputting source and include file lists:
~~~
waf dump_source
~~~
The file dumps will be in a subdirectory of build.  The name of this directory will be the name of the directory will be:

build/<dir_of_wscript>/work_dump/

## Currently Supported Simulation Environments

The simulation environment dictates what tools will be used when simulating designs.  The following list are values that can be set in the SFF_SIM_ENV variable to choose the respective environment.

- incisive
- modelsim

The following environments will be supported in future updates.

- iverilog


## Dependencies

The following tools must be installed for all simulation environments.

- [Veripool Verilog-Perl](https://www.veripool.org/wiki/verilog-perl)
  - Requires the command "vppreproc" to be on your path

### Incisive

The following tools must be installed for the incisive simulation environment.

### Modelsim

The following tools must be installed for the modelsim simulation environment.

### Iverilog

The following tools must be installed for the iverilog simuation environment.

