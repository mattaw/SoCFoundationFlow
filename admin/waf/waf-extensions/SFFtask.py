#! /usr/bin/env python
# encoding: utf-8
# Matthew Swabey, 2015
# John Skubic, 2017

"""
Classes and helper functions used to provide
"sim_source"
"verify_source"
"dump_source"
"dump_include"
"""

import os
from waflib import Context
from waflib import Build
from waflib import Logs
from waflib import Node
from waflib import TaskGen
from waflib import Task
from waflib import Utils
from waflib.Configure import conf
from waflib.TaskGen import feature, before_method, after_method
from SFFbuildmgr import SFF_verilog_scan
from SFFbuildmgr import SFFUnitsCont, SFFUnit, SFFView, load_SFFUnits
import pickle
# import needed simulation environments 
import SFFincisive
import SFFmodelsim

INCISIVE_ENV = 'incisive'
MODELSIM_ENV = 'modelsim'
VALID_ENVS = [INCISIVE_ENV, MODELSIM_ENV] 

def get_sim_env():
    """
    Checks the environment variables to decide the current simulation environment.
    """
    sim_env = os.environ.get('SFF_SIM_ENV')
    if not (sim_env in VALID_ENVS):
        print("Unexpected Simulation Environment: " + str(sim_env))
        print("Defaulting to " + VALID_ENVS[0])
        return VALID_ENVS[0]
    return sim_env

def configure(ctx):
    """
    Simulator: Find all the necessary parts of the chosen Simulator.
    """
    sim_env = get_sim_env()

    if sim_env == INCISIVE_ENV:
        SFFincisive.configure(ctx)
    elif sim_env == MODELSIM_ENV:
        SFFmodelsim.configure(ctx)    

class verify_source_ctx(Build.BuildContext):
    """
    Subclass waflib.Build.BuildContext to create a new command called
    verify_source. This command will is a placeholder and will run
    sim_source after setting the ctx.env['verify_source'] key.
    """
    cmd = 'verify_source'
    fun = 'verify_source'

Context.g_module.__dict__['verify_source_ctx'] = verify_source_ctx
"""
Inject the new verify_source command into the running waf build. Requires the
tool be loaded in the options section to make it exist in both configure and
build
"""

def verify_source(ctx):
    sim_env = get_sim_env()

    if sim_env == INCISIVE_ENV:
        SFFincisive._simulate(ctx, '-exit')
    elif sim_env == MODELSIM_ENV:
        SFFmodelsim._simulate(ctx, '-exit')

Context.g_module.__dict__['verify_source'] = verify_source
"""Inject the verify_source command into the wscript"""

class sim_source_ctx(Build.BuildContext):
    """
    Subclass waflib.Build.BuildContext to create a new command called
    sim_source.  This will operate exactly like a build command but find and
    execute functions from wscript files called 'sim_source'
    """
    cmd = 'sim_source'
    fun = 'sim_source'

Context.g_module.__dict__['sim_source_ctx'] = sim_source_ctx
"""
Inject the new sim_source command into the running waf build. Requires the tool
be loaded in the options section to make it exist in both configure and build
"""

def sim_source(ctx):
    sim_env = get_sim_env()

    if sim_env == INCISIVE_ENV:
        SFFincisive._simulate(ctx, '-gui')
    elif sim_env == MODELSIM_ENV:
        SFFmodelsim._simulate(ctx, '-gui')

Context.g_module.__dict__['sim_source'] = sim_source
"""Inject the sim_source command into the wscript"""

class dump_source_ctx(Build.BuildContext):
    cmd = 'dump_source'
    fun = 'dump_source'

Context.g_module.__dict__['dump_source_ctx'] = dump_source_ctx

def dump_source(ctx):
    #TODO: Implement dump_source
    pass

Context.g_module.__dict__['dump_source'] = dump_source

class dump_include_ctx(Build.BuildContext):
    cmd = 'dump_include'
    fun = 'dump_include'

Context.g_module.__dict__['dump_include_ctx'] = dump_include_ctx

def dump_include(ctx):
    #TODO: Implement dump_include
    pass

Context.g_module.__dict__['dump_include'] = dump_include


