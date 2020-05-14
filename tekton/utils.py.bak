

__author__ = "Ahmed El-Hassany"
__email__ = "a.hassany@gmail.com"


VALUENOTSET = 'EMPTY?Value'


def is_empty(var):
    """Return true if the variable is VALUENOTSET"""
    if hasattr(var, 'get_id'):
        return False
    return str(var) == VALUENOTSET or var is None


def is_symbolic(var):
    """Return true if the variable symbloic"""
    return hasattr(var, 'vsort')
