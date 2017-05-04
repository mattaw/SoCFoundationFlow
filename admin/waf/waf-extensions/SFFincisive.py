#! /usr/bin/env python
# encoding: utf-8
# Matthew Swabey, 2015

"""
Classes and helper functions used to provide
"sim_source"
"verify_source"
via the Cadence Incisive Suite.

TODO: Read book section 8.4.3
1) Create tasks using taskgen
2) Create function to prep strings and includes
3) Try to use the examples to find the files created by ncvlog inside the lib dir and add it to the deps to get proper dependency tracking and cleaning.
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
    Incisive: Find all the necessary parts of the Incisive Simulator.
    """
    ctx.find_program('ncvlog')
    ctx.find_program('ncvhdl')
    ctx.find_program('ncsim')
    ctx.find_program('ncelab')

def _simulate(ctx, gui):
    """
    Load the SFFUnits into the system.
    Create the necessary tasks to build the simulation libs
    Create a toplevel CDS.lib and hdl.var with the mappings for all the
    libraries and deps.
    Kick ncelab targetting the testbench
    Kick ncsim targetting the testbench
    """
    ctx.env['SFFUnits'] = load_SFFUnits(ctx)

    #units_taskgen(ctx)
    """
    Creates the directory path and nodes in the build directory.
    Creates the testbench library separately
    Creates a taskgen from each other library in units_hdl
    """

    top = ctx.env['SFFUnits'].getunit(ctx.env.top_level)

    for u in top.synu_deps + top.simu_deps:
        lib = u.script.parent.get_bld().make_node(u.name+'_nclib')
        lib.mkdir()
        u.b['nclib'] = lib

        if u.use('use'):
            tsk = IncisiveTask(
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
            tsk = IncisiveTask(
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
    tb_lib = top.script.parent.get_bld().make_node(top.use('tb')[0]+'_nclib')
    tb_lib.mkdir()
    top.b['tbnclib'] = tb_lib

    tsk = IncisiveTask(
        name=top.use('tb'),
        target=tb_lib,
        source=top.use('tb_src'),
        output=tb_lib,
        includes=top.use('tb_includes'),
        after=ctx.env.top_level,
        scan=SFF_verilog_scan,
        env=ctx.env )
    ctx.add_to_group(tsk)
    """
    Create the cds.lib and hdl.var in the toplevel of the build directory with
    the testbench defined in cds.lib and as WORKLIB in hdl.var.
    """
    build_cds_lib_file(ctx)
    build_hdl_var_file(ctx)

    top = ctx.env['SFFUnits'].getunit(ctx.env.top_level)
    #Run ncelab
    ctx(name='ncelab',
        rule='${NCELAB} -timescale ''1ns/10ps'' -access rwc %s' % top.use('tb')[0],
        always = True,)

    #Run ncsim
    ctx(name='ncsim',
        rule='${NCSIM} %s %s' % (gui,top.use('tb')[0]),
        always = True,
        after='ncelab')

class IncisiveTask(Task.Task):
    def __init__(self, *k, **kw):
        Task.Task.__init__(self, *k, **kw)

        self.dep_vars = ['VLOG_EXT']
        self.dep_vars += ['VHDL_EXT']
        self.dep_vars += ['SVLOG_EXT']
        self.dep_vars += ['SDC_EXT']

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
                incs += '-incdir ' + inc.bldpath() + ' '
        res = ''
        cmd = '%s -SV -linedebug -work %s %s %s' % (self.env['NCVLOG'][0], self.outputs[0],
            incs, src)
        return self.exec_command(cmd)


def build_cds_lib_file(ctx):
    top = ctx.env['SFFUnits'].getunit(ctx.env.top_level)
    cds_lib = ctx.path.make_node('cds.lib').get_bld()
    cds_lib.write('DEFINE {0} ./{1}\n'.format(top.b['tbnclib'],
        top.b['tbnclib'].bldpath()))
    for m in ctx.env['SFFUnits'].units:
        md = ctx.env['SFFUnits'].getunit(m)
        cds_lib.write('DEFINE {0} ./{1}\n'.format((md.b['nclib']),
            md.b['nclib'].bldpath()), flags='a')

def build_hdl_var_file(ctx):
    top = ctx.env['SFFUnits'].getunit(ctx.env.top_level)
    hdl_var = ctx.path.make_node('hdl.var').get_bld()
    hdl_var.write('DEFINE WORK {0}\n'.format(top.b['tbnclib']))
    hdl_var.write('DEFINE LIB_MAP (\\\n', flags='a')
    tb_dir = top.use('tb_dir')
    hdl_var.write('./{0}/... => {1}'.format(tb_dir.pop().bldpath(),
         top.b['tbnclib']), flags='a')
    if tb_dir:
        for d in tb_dir:
            hdl_var.write(',\\\n./{0}/... => {1}'.format(d.bldpath(),
                top.b['nclib']), flags='a')
    for m in ctx.env['SFFUnits'].units:
        md = ctx.env['SFFUnits'].getunit(m)
        for d in md.use('src_dir'):
            hdl_var.write(',\\\n./{0}/... => {1}'.format(d.bldpath(),
                md.b['nclib']), flags='a')
    hdl_var.write(')\n', flags='a')

