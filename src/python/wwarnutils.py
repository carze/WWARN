#!/usr/bin/env python

##
# This module contains utility functions that are used across the WWARN 
# calculation scripts
#
import MySQLdb
import datetime

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

def validateGenotypes(genotypes, invalidGenotypes=['not genotyped', 'genotyping failure']):
    """
    Validates our genotypes to ensure that they do not fall in one of 
    the passed in invalid genotypes. 
    """
    validBool = True
    
    for genotype in genotypes:
        try:
            if genotype.lower() in invalidGenotypes:
                validBool = False            
                break
        except AttributeError as e:
            pass

    return validBool

def open_db_connection(hostname, db_name, username, password):
    """
    Opens a connection to the database specified by the passed in arguments
    to this function
    """
    db_conn = MySQLdb.connect(host=hostname, user=username, passwd=password, db=db_name)
    return db_conn

def create_year_bins(step, bounds):
    """
    Creates a list of tuples containing the pots to bin all our studies 
    when creating calculations. Each tuple will contain datetime objects
    containing the bounds of the bin, i.e. ('2007-02-01', '2009-02-01')
    """
    year_bins = {}

    for (label, site, lower, upper) in bounds:
        year_bins.setdefault(label, {})[site] = (date_range(lower, upper, datetime.timedelta(365 * step)))
        
    return year_bins 
                
def date_range(start, stop, step):
    """
    Generates a range of dates in the format (A, B), (B, C), (C, D) etc.
    """
    output = []

    if start < stop:
        cmp = lambda a, b: a < b
        inc = lambda a: a + step
    else:
        cmp = lambda a, b: a > b
        inc = lambda a: a - step

    while cmp(start, stop):
        end = inc(start)
        output.append( (start, end) )  
        start = end
    
    return output        

def get_db_date_bounds(conn, query_components, params):
    """
    Gets the lower and upper bound dates for each project - site combination
    in the WWARN db.
    """
    cursor = conn.cursor()

    query = "SELECT s.label, l.site, MIN(p.date_of_inclusion), MAX(p.date_of_inclusion) " + query_components[1] + query_components[2]
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()           
    
    for row in rows:
        yield row

def get_template_date_bounds(template_fh):
    """
    Gets the lower and upper bound dates for each project - site combination
    in a WWARN template file.
    """
    bounds = {} 
    
    # We need to loop over our file once to grab the bounds for each of our 
    # project - site combinations.
    for row in template_fh:
        if all(s == '\t' for s in row.rstrip('\r\n')) or row.startswith('#'):
            continue

        row = row.rstrip('\n\r').split('\t')            
        label = row[2]
        country = row[3]
        site = row[4]                    

        doi = datetime.datetime.strptime(row[7], '%Y-%m-%d')

        bounds.setdefault((label, site), {})
        lower = bounds.get((label, site)).get('lower', None)
        upper = bounds.get((label, site)).get('upper', None)
        
        if lower == None or doi < lower:
            bounds[(label, site)]['lower'] = doi

        if upper == None or doi > upper:
            bounds[(label, site)]['upper'] = doi
 
    # Reset the file handle to the beginning of the file
    template_fh.seek(0, 0)

    # Now we want to create a list comprehension generator to yield this information
    for metadata in bounds:
        yield [metadata[0], metadata[1], bounds.get(metadata).get('lower'),
               bounds.get(metadata).get('upper')]

def parse_site(site, label, doi, year_bins):
    """
    Attempts to bin a site using the generate year ranges if they were 
    generated otherwise returns the site untouched.
    """
    if year_bins:
        site_bins = year_bins[label][site]
        for (lower, upper) in site_bins:
            if lower <= doi < upper:
                site = "%s_%s-%s" % (site, lower.year, upper.year)
    
    return site 
