
class AgeGroupException(Exception):
    """ 
    A custom exception class that should be raised when an age
    group provided is not well-formed
    """
    def __init__(self, value):
        self.error_msg = value
        
    def __str__(self):
        return repr(self.error_msg) 
 
class CopyNumberGroupException(Exception):
    """ 
    A custom exception class that should be raised when an age
    group provided is not well-formed
    """
    def __init__(self, value):
        self.error_msg = value
        
    def __str__(self):
        return repr(self.error_msg) 
