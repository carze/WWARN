#!/usr/bin/env python

##
# This module contains utility functions that are used across the WWARN 
# calculation scripts
#
from collections import OrderedDict
from pprint import pprint as pp_pprint
from wwarnexceptions import AgeGroupException, CopyNumberGroupException

def parseAgeGroups(groupsFile):
    """
    Parses the provided age groups file and returns a list of tuples containing the
    desired age groups for the accompanying WWARN data to be binned into

    Input file should be a tab-delimited file of the following format:
       
       <LOWER BOUNDS>\\t<UPPER BOUNDS>\\t<LABEL>
       None\\t\\t1< 1
       1\\t4\\t1-4

    First column contains lower bound of group, second column contains upper bound of group
    while the third column contains the name that should act as the key in the dictionary 
    containing results returned by our calculations library.

    Returned list is of the following format:
        
       [ (<LOWER>, <UPPER>, <LABEL>), (<LOWER>, <UPPER>, <LABEL) ... ]
    """
    ageList = []

    groupsFH = open(groupsFile)
    for line in groupsFH:
        if line.startswith('#'): continue
        (lower, upper, name) = line.rstrip('\n').split('\t')
        
        # Cast our variables to float if they are not 'None'
        # And None if they are 'None'
        if lower == 'None':
            lower = None
            upper = float(upper)
        elif upper == 'None':
            upper = None
            lower = float(lower)
        elif upper == 'None' and lower == 'None':
            raise AgeGroupException('Cannot have "lower" and "upper" values both set to None in an age group') 
        else:
            lower = float(lower)
            upper = float(upper)

        ageList.append( (lower, upper, name) )

    return ageList

def parseCopyNumberGroups(groupsFile):
    """
    Parses the optional list of groups that copy number data should be binned into.
    This file should be formatted like so:

        #GROUP_NAME\tLOWER\tUPPER
        1\t0.50\t1.49

    Our first column contains the name of the group, which will be the representative value for anything data
    binned into this group. The second and third columns establish the lower and upper bounds of this group,
    any data falling in between these two bounds should be captured into this group.        
    """
    copyNumGroups = []

    copyNumFH = open(groupsFile)
    for line in copyNumFH:
        if line.startswith('#'): continue
        (groupName, lower, upper) = line.rstrip('\n').split('\t')

        if lower == 'None':
            lower = None
            upper = float(upper)
        elif upper == 'None':
            upper = None
            lower = float(lower)
        elif upper == 'None' and lower == 'None':
            raise CopyNumberGroupException('Cannot have "lower" and "upper" values both set to None in a copy number group') 
        else:
            lower = float(lower)
            upper = float(upper)

        copyNumGroups.append( (groupName, lower, upper) )

    return copyNumGroups        

def preBinCopyNumberData(copyNum, bins):
    """
    Based off groups provided via command-line argument copy number data will be 
    binned into a proper group. E.x.:

    CN = 1 (copy number data falls between 0.50 - 1.49)
    CN = 2 (copy number data falls between 1.50 - 2.49)
    """
    binName = None

    for bin in bins:
        (name, lower, upper) = bin

        if lower is None:
            if float(copyNum) < upper:
                binName = name
                break

        if upper is None:
            if float(copyNum) > lower:
                binName = name
                break

        if lower is not None and upper is not None:    
            if lower <= float(copyNum) <= upper:
                binName = name
                break


    if binName is None:
        # If no group name is found we will just round up to the next nearest whole number.
        # TODO: Check what proper behaviour should be here
        binName = '%s' % ( int( round( float(copyNum) ) ) )

    return binName


def pprint(obj, *args, **kwrds):
    """
    Override the stock pprint function to work with OrderedDictionaries
    Credit to martineau @ StackOverflow

    http://stackoverflow.com/questions/4301069/any-way-to-properly-pretty-print-ordered-dictionaries-in-python
    """
    if not isinstance(obj, OrderedDict):
        # use stock function
        return pp_pprint(obj, *args, **kwrds)
    else:
        # very simple sample custom implementation...
        print "{"
        for key in obj:
            print "    %r:%r" % (key, obj[key])
        print "}"
