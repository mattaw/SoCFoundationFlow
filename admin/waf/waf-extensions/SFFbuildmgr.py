#! /usr/bin/env python
# encoding: utf-8
# Matthew Swabey, 2015
# Matthew Swabey, 2016

"""
Classes and helper functions used to build the Foundation Flow.
Anything that is used by more than one tool lives here.

TODO:
3) Make it work with Incisive.
4) Consider using a +view notation to add a view to existing views.
"""

from waflib.Configure import conf
from waflib import Build
from waflib import Logs
from waflib import Utils
from waflib import Errors
from waflib import Context
from waflib import Options
from waflib import Node
import pickle
import os.path
import sys
import SFFutil
import SFFerrors


def options(ctx):
    ctx.add_option('--top_level', action='store',
                   help=('Set the root unit of the design'))

    ctx.add_option('--views', action='store', default='default',
                   help=('Set an ordered, comma-separated, list of views to '
                         'supply to the command.'))

    ctx.add_option('--check', action='store_true', default=False,
                   help=('Check all units for correctness.'))

def configure(ctx):
    if not ctx.options.top_level:
        raise Errors.ConfigurationError(
            'SoCManager: Please set a top level unit by running waf '
            'configure --top_level=<top_level>')
    ctx.env['top_level'] = ctx.options.top_level
    ctx.env['views'] = ctx.options.views
    ctx.env['check'] = ctx.options.check

    """Create class in the context to hold/manipulate the SFFUnits."""
    ctx.SFFUnits = ctx.SFFUnitsCont()

    """File extensions to compile as Verilog."""
    ctx.env.VLOG_EXT = ['.v']
    """File extensions to compile as VHDL."""
    ctx.env.VHDL_EXT = ['.vhdl', '.vhd']
    """File extensions to compile as System Verilog."""
    ctx.env.SVLOG_EXT = ['.sv']
    """File extensions to identify Synopsys Design Constraints (SDC) files."""
    ctx.env.SDC_EXT = ['.sdc']

    """
    Static version of Perl vppreproc http://www.veripool.org/ used to parse
    verilog for headers.
    """
    ctx.find_program('vppreproc')

@conf
class SFFUnitsCont():
    """
    Class to store and manipulate SFFUnit objects.
    """
    def __init__(self, ctx):
        """
        Create an empty dictionary to store the units.
        Store the ctx where we were created for later.
        """
        self.check = ctx.env['check']
        self.ctx = ctx
        self.units = {}
        self.top_level = ctx.env['top_level']
        self._packed = False
        self.views = SFFutil.strtolist(ctx.env['views'])
        self.synu_deps = []
        self.simu_deps = []

    def getunit(self, unit):
        if isinstance(unit, list):
            return [self.units.get(u) for u in unit]
        else:
            return self.units[unit]

    def add(self, *args, **kwargs):
        """
        Creates a SFFUnit and inserts it into the unit dictionary if there
        isn't already an existing one.
        """
        unit = self.ctx.SFFUnit(*args, **kwargs)

        if unit.name in self.units:
            raise Errors.ConfigurationError(
                ("SoCManager: Error. Module names must be unique. Module '{0}'"
                 " from script '{1}' already defined by script '{2}'").format(
                    unit.name, self.ctx.cur_script.srcpath(),
                    self.getunit(unit.name).script.srcpath()))
        self.units[unit.name] = unit

    def addview(self, name, view, **kwargs):
        if name not in self.units:
            raise Errors.ConfigurationError(
                ("SoCManager: Error. Cannot find Module '{0}'"
                 " from script '{1}' to add view '{2}'").format(
                    name, self.ctx.cur_script.srcpath(), view))
        else:
            self.units[name].addview(view, **kwargs)

    def _buildunitdeps(self, unit_order, unit):
        """
        Order a list which can be built from left to right to build all
        units from a dictionary of named units which have
        a subkey 'use' referring to other named prerequisite units.
        If memory becomes a problem then change to iterative from recursion.
        """
        if unit in unit_order:
            return unit_order
        elif 'use' in self.units[unit]._k.keys():
            for u in self.units[unit]._k.use('use'):
                try:
                    unit_order = self._buildunitdeps(unit_order, u)
                except KeyError:
                    raise Errors.ConfigurationError(('Unit \'{0}\''
                        ' required by \'{1}\' defined in \'{2}\' has not been'
                        ' defined.').format(u, unit,
                            self.units[unit].script.srcpath()) )

        unit_order.append(unit)
        return unit_order

    def get_unit_deps(self, name):
        """
        Starting at unit 'name' generate two lists of deps in leaf first order
        """
        synu_deps = self._buildunitdeps([], name)

        simu_deps = []
        if 'tb_use' in self.units[name]._k.keys():
            for tb_dep in self.units[name]._k.use('tb_use'):
                simu_deps = self._buildunitdeps(simu_deps, tb_dep)
        simu_deps = [u for u in simu_deps if u not in synu_deps]

        return synu_deps, simu_deps

    def finalize(self):
        """
        If --check is not defined:
        1) Process the unit views' inheritance on the use and use_tb keys
        2) Search the unit tree from the top and build the dependency order
            from --top_level unit for syn and sim using use and use_tb
        3) Drop unused units from self.units to save memory and processing
        4) Process the unit views' inheritance on remaining keys
        5) Pickle internal state where necessary and store to env['SFFUnits']

        if --check is defined:
        1) Check every view of every unit
        2) Go back to 1) above
        TODO 1.5) Walk all deps

        """

        # Test the existence of the top_level unit key
        try:
            self.getunit(self.top_level)
        except KeyError:
            raise Errors.ConfigurationError(('Top Level "{0}" not'
                ' found. Please re-run "waf configure --top_level= " with the'
                ' correct top_level name or check the unit names and recurses'
                ' in your wscript files.').format(self.top_level))

        if self.check:
            self.ctx.msg('Option', '--check', color='BLUE')
            for m in self.units:
                self.units[m].check_all()

        # Apply inheritance on the use and tb_use directives
        for name,unit in self.units.items():
            self.units[name].applyinheritance(self.views, ('use','tb_use'))

        # Get the top_level unit dependencies from the use and tb_use keys
        synu,simu = self.get_unit_deps(self.top_level)
        self.synu_deps = synu
        self.simu_deps = simu

        # Prune the SFFUnits dictionary to only syn and sim units
        self.units = dict((k, self.units[k])
             for k in simu + synu)

        # Apply inheritance on all keys
        for name,unit in self.units.items():
            self.units[name].applyinheritance(self.views)

        # Get and store the unit dependencies from the use and tb_use keys
        for name,unit in self.units.items():
            synu,simu = self.get_unit_deps(name)
            self.units[name].set_deps(self.getunit(synu), self.getunit(simu))

        self.ctx.msg('top_level set to', '{0}'.format(self.top_level),
            color='BLUE')
        self.ctx.msg('Units for simulation', '{0}'.format(self.simu_deps),
            color='BLUE')
        self.ctx.msg('Units for synthesis', '{0}'.format(self.synu_deps),
            color='BLUE')

        # Context contains one or more waflib.Nodes.Nod3 which cannot be
        #  pickled so we have to get rid of it. Also the configuration
        #  context is not valid in build etc.
        for m in self.units:
            self.units[m].pack()
        env = self.ctx.env
        delattr(self,'ctx')
        env['SFFUnits'] = pickle.dumps(self)
        self._packed = True

    def unpack(self, ctx):
        self.ctx = ctx
        for name,unit in self.units.items():
            unit.unpack(ctx)
        self._packed = False

def load_SFFUnits(ctx):
    new_SFFUnits = pickle.loads(ctx.env['SFFUnits'])
    new_SFFUnits.ctx = ctx
    for name,unit in new_SFFUnits.units.iteritems():
        unit.unpack(ctx)
    return new_SFFUnits


@conf
class SFFUnit:
    def __init__(self, ctx, *args, **kwargs):
        """
        Create a SFFUnit object.
        """
        cur_view = 'default'

        try:
            if len(args) == 2:
                if isinstance(args[0], str) and isinstance(args[1], str):
                    self.name = args[0]
                    cur_view = 'args[1]'
            if len(args) == 1:
                if isinstance(args[0], str):
                    self.name = args[0]
            elif len(args) == 0:
                self.name = str(ctx.path)
            else:
                raise
        except:
            raise ctx.errors.ConfigurationError(
                'Malformed SFFUnit() in: {0}.\n{1}'.format(
                    ctx.cur_script.srcpath(), ctx.cur_script.read()))

        self.ctx = ctx
        self._packed = False
        self._check = False
        self.simu_deps = []
        self.synu_deps = []

        #Script that created us
        self.script = ctx.cur_script
        #Dictionary for the different views
        self._v = {}
        #Post inheritance view
        self._k = SFFView(self)
        #Dictionary for build keys that are attached by other tools
        self.b = {}

        self.addview(cur_view, **kwargs)

    def __repr__(self):
        string = "SFFUnit {0}\n".format(self.name)
        string.join('{}{}'.format(key, val) for key, val in self.__dict__.items())
        return string

    def addview(self, view, **kwargs):
        if view in self._v:
            raise Errors.ConfigurationError(
                ("SoCManager: Error. View names must be unique. Module '{0}'"
                 " from script '{1}' already has view '{2}'").format(
                    self.name, self.script.srcpath(), view))

        #Create & store the kwargs into the view
        self._v[view] = SFFView(self, **kwargs)

    def applyinheritance(self, views, keys = None):
        """
        1) Go through the --views in the order specified in the list views.
        2) Test the first char to see if it is '+'
        3) If keys is a list process only them. If keys = False process all
           keys.
        Note if a view doesn't have a '+' we are simply overwriting data from           other views. If it is a '+view' we append to existing keys and create
        new ones. We apply str -> list conversion here "on demand"
        """

        for view in views:
            addview = False
            if view[0] is '+':
                view = view[1:]
                addview = True

            if view in self._v:
                if keys:
                    keys_ck = keys
                else:
                    keys_ck = self._v[view].keys()
                for k in keys_ck:
                    if addview is False:
                        if k in self._v[view].keys():
                            newkey = SFFutil.strtolist(self._v[view].get(k))
                            self._k.add(k, newkey)
                    else:
                        if k not in self._k.keys() and k in self._v[view].keys():
                            newkey = SFFutil.strtolist(self._v[view].get(k))
                            self._k.add(k, newkey)
                        elif k in self._k.keys() and k in self._v[view].keys():
                            newkey = SFFutil.strtolist(self._v[view].get(k))
                            oldkey = self._k.get(k)
                            self._k.add(k, oldkey + newkey)

    def check_all(self):
        """
        Check all views
        """
        if self._check:
            raise Errors.ConfigurationError(
                "'{0}': Error. Module has already been checked.".format(
                self.name))
        else:
            self._check = True

        try:
            for v in self._v:
                self._v[v].check()
        except SFFerrors.Error as e:
            raise Errors.ConfigurationError(
                ("Module '{0}': Error. View '{1}' failed check with "
                 "message: {2}".format(self.name, v, e.msg)))

    def pack(self):
        env = self.ctx.env
        self.script = self.script.srcpath()
        delattr(self,'ctx')
        self._k.pack()
        for view in self._v:
            self._v[view].pack()
        self._packed = True

    def unpack(self, ctx):
        self.ctx = ctx
        self.script = ctx.path.make_node(self.script)
        self._k.unpack(self)
        for view in self._v:
            self._v[view].unpack(self)
        self._packed = False

    def use(self, key):
        if key == 'includes':
            nodes = set()
            if self.synu_deps:
                for u in self.synu_deps:
                    nodes.update(u.use('_includes'))
            if self.use('_includes'):
                nodes.update(self.use('_includes'))
            if nodes:
                return nodes
            else:
                raise SFFerrors.Error("Key includes not set")
        elif key == 'tb_includes':
            nodes = set()
            if self.simu_deps:
                for u in self.simu_deps:
                    nodes.update(u.use('_tb_includes'))
            if self.use('_tb_includes'):
                nodes.update(self.use('_tb_includes'))
            if self.use('includes'):
                nodes.update(self.use('includes'))
            if nodes:
                return nodes
            else:
                raise SFFerrors.Error("Key includes not set")
        else:
            return self._k.use(key)

    def get(self, key):
        return self._k.get(key)

    def add(self, key, thing):
        self._k.add(key, thing)

    def set_deps(self, synu, simu):
        self.synu_deps = synu
        self.simu_deps = simu

@conf
class SFFView():
    """
    NEW PLAN:
    Hold the user settings from the file.
    On-the-fly generate what is asked using those to drive the algo. Forget
        caching them in dicts or anything like that.
    """

    def __init__(self, unit, **kwargs):
        self.unit = unit
        self._k = {}

        for key,val in kwargs.items():
            self._k[key] = SFFutil.strtolist(val)

    def __repr__(self):
        key_str = ''
        for key in self._validkeys:
            key_str += str(key) + ': ' + str(self.use(key)) + '\n'
        return ("SFFView contents:\n" + key_str)

    _validkeys = ('name','unit_top','use','src_dir','src','_includes',
        'tb_dir','tb_src','_tb_includes','tb','tb_use')

    def check(self):
        for key in self._validkeys:
            self.use(key)

    def keys(self):
        return self._k.keys()

    def validkeys(self):
        return self._validkeys

    def get(self, k):
        return self._k.get(k)

    def add(self, k, thing):
        self._k[k] = thing

    def extend(self, k, thing):
        self._k[k].extend(thing)

    def use(self, key):
        hdl_ext = []
        hdl_ext += self.unit.ctx.env.VLOG_EXT
        hdl_ext += self.unit.ctx.env.SVLOG_EXT
        hdl_ext += self.unit.ctx.env.VHDL_EXT

        if key == 'name':
            return [self.unit.name]
        if key == 'unit_top':
            if self.get(key):
                return self.get(key)
            else:
                return self.use('name')
        if key == 'use':
            return self.get(key)
        if key == 'tb_use':
            return self.get(key)
        if key == 'src':
            nodes = set()
            if self.get('src'):
                nodes.update(self._getnodes(self.get('src'), False))
            if self.get('src_dir'):
                nodes.update(self._searchnodes(self.get('src_dir'), hdl_ext,
                    False)[0])
            else:
                nodes.update(self._searchnodes(['src'], hdl_ext)[0])
            return nodes
        if key == 'src_dir':
            nodes = set()
            if self.get('src_dir'):
                nodes.update(self._getnodes(self.get('src_dir'), False))
            else:
                nodes.update(self._getnodes(['src']))
            return nodes
        if key == 'tb_src':
            nodes = set()
            if self.get('tb_src'):
                nodes.update(self._getnodes(self.get('tb_src'), False))
            if self.get('tb_dir'):
                nodes.update(self._searchnodes(self.get('tb_dir'), hdl_ext,
                    False)[0])
            else:
                nodes.update(self._searchnodes(['tb'], hdl_ext)[0])
            return nodes
        if key == 'tb_dir':
            nodes = set()
            if self.get('tb_dir'):
                nodes.update(self._getnodes(self.get('tb_dir'), False))
            else:
                nodes.update(self._getnodes(['tb']))
            return nodes
        if key == '_includes':
            nodes = set()
            if self.get('includes'):
                nodes.update(self._getnodes(self.get('includes'), False))
            else:
                nodes.update(self.use('src_dir'))
            return nodes
        if key == '_tb_includes':
            nodes = set()
            if self.get('tb_includes'):
                nodes.update(self._getnodes(self.get('tb_includes'), False))
            else:
                nodes.update(self.use('src_dir'))
                nodes.update(self.use('tb_dir'))
            return nodes
        if key == 'tb':
            if self.get('tb'):
                return self.get('tb')
            else:
                return ['tb_'+self.use('name')[0]]
        else:
            raise SFFerrors.Error("Key {0} not understood".format(key))

    def _getnodes(self, list_, silentfail=True):
        nodes = set()
        dir_ = self.unit.script.parent
        for name in list_:
            n = dir_.find_node(name)
            if n in nodes:
                raise SFFerrors.Error("File or dir: {0} already specified"
                    .format(dir_.srcpath() + '/' + name))
            elif n is not None:
                nodes.add(n)
            elif not silentfail:
                raise SFFerrors.Error("File or dir: {0} not found"
                    .format(dir_.srcpath() + '/' + name))
        return nodes

    def _searchnodes(self, list_, ext='.*', silentfail=True):
        #Try to create node before search!
        dirnodes = set()
        for d in list_:
            node = self.unit.script.parent.find_node(d)
            if node:
                dirnodes.add(node)
            elif not silentfail:
                raise SFFerrors.Error("Directory {0} not found".format(d))

        filenodes = set()
        dirnodeswithsrc = set()

        for d in dirnodes:
            new_files = []
            for e in ext:
                new_files += d.ant_glob('**/*{0}'.format(e))
            for n in new_files:
                filenodes.add(n)
            if new_files:
                dirnodeswithsrc.add(d)
            else:
                if not silentfail:
                    raise SFFerrors.Error(("Directory {0} contained no sources "
                        "ending in: {1}".format(d, ext)))

        return filenodes,dirnodeswithsrc

    def pack(self):
        delattr(self, 'unit')
        pass #self.unit = self.unit.abspath()

    def unpack(self, unit):
        self.unit = unit
        pass

@conf
def setup_hdl_module(self, *args, **kwargs):
    self.msg('SFFUnits.setup_hdl_module() depreciated', ('Replace with '
                 'SFFUnits.add()'), color='YELLOW')
    self.SFFUnits.add(*args, **kwargs)

def load_SFFUnits(ctx):
    new_SFFUnits = pickle.loads(ctx.env['SFFUnits'])
    new_SFFUnits.ctx = ctx
    new_SFFUnits.unpack(ctx)
    return new_SFFUnits

import re, sys, os
def SFF_verilog_scan(task):
    """
    scan for dependencies using the Veripool vppreprocessor tool.  Execute the
    preprocessor using the includes and collect the output. Then grep it for
    `line directives, extract the file name and add to a set to eliminate
    duplicates. Then convert the list to nodes and return.
    """
    env = task.env
    gen = task.generator
    bld = gen.bld
    wd = bld.bldnode.abspath()
    exec_env = {}
    cmd = []
    cmd.extend(['vppreproc'])
    #Ugly hack here as includes are not propagated into the task
    if(hasattr(gen, 'includes')):
            includes = [a.path_from(bld.bldnode) for a in gen.includes]
            for include in includes:
                    cmd.extend(['-y',include])
    files = [a.path_from(bld.bldnode) for a in task.inputs]
    cmd += files

    out = bld.cmd_and_log(cmd, cwd=bld.variant_dir, quiet=Context.BOTH)

    #Match the `line directives
    lst_src = []
    seen = set([])
    line_det = re.compile(r'`line.*"(.*)"')
    for x in Utils.to_list(line_det.findall(out)):
            if x in files:
                    seen.add(x)
            if x in seen or not x:
                    continue
            seen.add(x)
            if os.path.isabs(x):
                    lst_src.append(bld.root.make_node(x) or x)
            else:
                    p = bld.path.get_bld().make_node(x)
                    lst_src.append(p)
    return (lst_src, [])


