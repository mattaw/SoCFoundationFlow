#! /usr/bin/env python
# encoding: utf-8
# Matthew Swabey, 2015
# John Skubic, 2017

"""
Classes and helper functions used to provide
"sim_source"
"verify_source"
"dump_source"
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

SRC_DUMP = 'srcs.dump'
INC_DUMP = 'incs.dump' 

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
        SFFmodelsim._simulate(ctx, '-c -do "run -a;q"')

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
        SFFmodelsim._simulate(ctx, '')

Context.g_module.__dict__['sim_source'] = sim_source
"""Inject the sim_source command into the wscript"""

class dump_source_ctx(Build.BuildContext):
    cmd = 'dump_source'
    fun = 'dump_source'

Context.g_module.__dict__['dump_source_ctx'] = dump_source_ctx

def dump_source(ctx):
    """ 
    Load the SFFUnits into the system. 
    Output each file to standard out.
    """
    ctx.env['SFFUnits'] = load_SFFUnits(ctx)

    """
    Creates the directory path and nodes in the build directory.
    Creates a taskgen from each other library in units_hdl
    """
    top = ctx.env['SFFUnits'].getunit(ctx.env.top_level)

    """
    Ensure the output files are all cleared before running the command
    to prevent duplicate files in the output.
    """
    for u in top.synu_deps + top.simu_deps:
      lib = u.script.parent.get_bld().make_node('work_dump')
      src_file = ctx.out_dir + '/' + lib.bldpath() + '/' + SRC_DUMP
      inc_file = ctx.out_dir + '/' + lib.bldpath() + '/' + INC_DUMP
      try:
        os.remove(src_file)
      except:
        pass
      try:
        os.remove(inc_file)
      except:
        pass
      
  
    for u in top.synu_deps + top.simu_deps:
      lib = u.script.parent.get_bld().make_node('work_dump')
      lib.mkdir()
      
      if u.use('use'):
        tsk = DumpTask(
          name=u.name,
          source=u.use('src'),
          includes=u.use('includes'),
          after=u.use('use'),
          output=lib,
          scan=SFF_verilog_scan,
          env=ctx.env)
        ctx.add_to_group(tsk) 
      else:
        tsk = DumpTask(
          name=u.name,
          source=u.use('src'),
          includes=u.use('includes'),
          output=lib,
          scan=SFF_verilog_scan,
          env=ctx.env)
        ctx.add_to_group(tsk)

Context.g_module.__dict__['dump_source'] = dump_source

class DumpTask(Task.Task):
    def __init__(self, *k, **kw):
        Task.Task.__init__(self, *k, **kw)

        self.set_inputs(list(kw['source']))
        self.set_outputs(kw['output'])
        self.includes = kw['includes']
        from types import MethodType
        self.scan = MethodType(kw['scan'],self)

    def __str__(self):
        return '%s: %s\n' % (self.__class__.__name__,self.outputs[0])

    def run(self):
        src = ''
        for s in self.inputs:
            src += s.bldpath() + '\n'
        tgt = self.outputs[0].bldpath()
        incs = ''
        if hasattr(self.generator,'includes'):
            incs = ''
            for inc in getattr(self.generator,'includes'):
              incs += inc.bldpath() + '\n'
        src_file = self.outputs[0].bldpath()+'/'+ SRC_DUMP
        inc_file = self.outputs[0].bldpath()+'/'+ INC_DUMP
        cmd_src = "echo '%s' >> %s" % (src, src_file)
        cmd_include = "echo '%s' >> %s" % (incs, inc_file)
        cmd = "%s;%s" % (cmd_src, cmd_include)
        
        return self.exec_command(cmd)
