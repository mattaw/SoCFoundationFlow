from waflib import Errors
from waflib import Node
import SFFerrors

def strtolist(string_or_list):
    if isinstance(string_or_list, str):
        return [s.strip() for s in string_or_list.split(',')]
    elif isinstance(string_or_list, (list, set)):
        return string_or_list
    raise SFFerrors.Error(
        ("strtolist passed type: '{0}' instead of str or list")
            .format(type(string_or_list)))
    
def list2nodes(self, subdir, list_, silent_fail):
    nodes = set()
    for file_ in list_:
        n = subdir.find_node(file_) 
        if n in nodes:
            raise Errors.ConfigurationError(
                "'{0}': Node '{1}' already exits in list '{2}'.".format(
                    self.name, subdir.srcpath() + '/' + n, list_))
        elif n is not None:
            nodes.add(n)
        elif not silent_fail:
            raise Errors.ConfigurationError(
                "'{0}': Failed to find '{1}' on disk.".format(
                    self.name, subdir.srcpath() + '/' + node))
    return nodes
