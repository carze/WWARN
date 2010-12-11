##
# A simple class that mimics the perl autovivification mechanism in
# python.
#
# All credit goes to nosklo from Stack Overflow:
#
#  http://stackoverflow.com/questions/635483/what-is-the-best-way-to-implement-nested-dictionaries-in-python/652284#652284
#

class AutoVivification(dict):
    """Implementation of perl's autovivification feature."""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value
