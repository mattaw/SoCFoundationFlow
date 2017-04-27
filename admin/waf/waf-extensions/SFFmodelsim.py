#! /usr/bin/env python
# encoding: utf-8
# John Skubic, 2017

"""
Classes and helper functions used to provide
"sim_source"
"verify_source"
via the Mentor Graphics Modelsim suite
"""

from waflib import Context
from waflib import Build
from waflib import Logs
from waflib import Node
from waflib import TaskGen
from waflib import Task
from waflib import Utils
from waflib.Configure import conf
from waflib.TaskGen import feature, before_method, after_method
import pickle
import os,sys
from SFFbuildmgr import SFF_verilog_scan
from SFFbuildmgr import SFFUnitsCont, SFFUnit, SFFView, load_SFFUnits

def configure(ctx):
    """
    Modelsim: Find all the necessary parts of the Modelsim Simulator.
    """
    ctx.find_program('vlog')
    ctx.find_program('vcom')
    ctx.find_program('vlib')
    ctx.find_program('vsim')

def _simulate(ctx, gui):
    """
    Load the SFFUnits into the system.
    Create the necessary tasks to build the simulation libs
    Kick vsim targetting the testbench
    """
    ctx.env['SFFUnits'] = load_SFFUnits(ctx)

    """
    Creates the directory path and nodes in the build directory.
    Creates a taskgen from each other library in units_hdl
    """

    top = ctx.env['SFFUnits'].getunit(ctx.env.top_level)

    for u in top.synu_deps + top.simu_deps:
        lib = u.script.parent.get_bld().make_node('work_vlib')
        lib.mkdir()
        u.b['vlib'] = lib

        if u.use('use'):
            tsk = ModelsimTask(
                name=u.name,
                target=lib,
                source=u.use('src'),
                includes=u.use('includes'),
                after=u.use('use'),
                output=lib,
                scan=SFF_verilog_scan,
                env=ctx.env)
            ctx.add_to_group(tsk)
        else:
            tsk = ModelsimTask(
                name=u.name,
                target=lib,
                source=u.use('src'),
                output=lib,
                includes=u.use('includes'),
                scan=SFF_verilog_scan,
                env=ctx.env)
            ctx.add_to_group(tsk)


    """
    Create the testbench taskgen last as it is always at the top dep
    """
    ctx.add_group()
    tb_lib = top.script.parent.get_bld().make_node('work_vlib')
    tb_lib.mkdir()
    top.b['tbvlib'] = tb_lib

    tsk = ModelsimTask(
        name=top.use('tb'),
        target=tb_lib,
        source=top.use('tb_src'),
        output=tb_lib,
        includes=top.use('tb_includes'),
        after=ctx.env.top_level,
        scan=SFF_verilog_scan,
        env=ctx.env )
    ctx.add_to_group(tsk)
    ctx.add_group()

    """
    Run the Modelsim command with gui options provided.
    """
    ##Run vsim
    print("TBSRC : " + str(top.use('tb_src')))
    ctx(name='vsim',
        rule='vsim %s -lib %s %s' % (gui,top.b['tbvlib'], top.use('tb')[0]),
        always = True)

class ModelsimTask(Task.Task):
    def __init__(self, *k, **kw):
        Task.Task.__init__(self, *k, **kw)

        self.set_inputs(list(kw['source']))
        self.set_outputs(kw['output'])
        self.includes = kw['includes']
        self.before = ['ncelab','ncsim']
        from types import MethodType
        self.scan = MethodType(kw['scan'],self)


    def __str__(self):
        return '%s: %s\n' % (self.__class__.__name__,self.outputs[0])

    def run(self):
        src = ''
        for s in self.inputs:
            src += s.bldpath() + ' '
        tgt = self.outputs[0].bldpath()
        incs = ''
        if hasattr(self.generator,'includes'):
            incs = ''
            for inc in getattr(self.generator,'includes'):
                incs += '+incdir+' + inc.bldpath() + ' '
        res = ''
        cmd_setup = 'vlib %s; ' % (self.outputs[0])
        cmd = '%s vlog -sv -work %s %s %s' % (cmd_setup, self.outputs[0],
            incs, src)
        return self.exec_command(cmd)
