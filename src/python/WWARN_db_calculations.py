#!/usr/bin/env python

##
# This script (soon to be CGI script) queries the back-end WWARN database to perform a 
# calculation on either a specific dataset pulled from the database (query with criteria)
# or the full set of data from the database.
#

import os,
import MySQLdb
import argparse

from collections import OrderedDict
from wwarnutils import parseAgeGroups, parseCopyNumberGroups, preBinCopyNumberData

def buildArgParser():
    """
    Builds an argparse object used to parse any command-line arguments passed
    into the script.
    """
    parser = argparse.ArgumentParser(description="Produces sample size and prevalence calculations "
                        + "given data provided from the WWARN database")
    parser.add_argument("-c", "--config_file", required=True, help="The datbase configuration file "
                        + "containing database login credentials")
    parser.add_argument("-m", "--marker_list", required=True, help="A list of all possible markers "
                        + "that should be present in our output")
    parser.add_argument("-mc" "--marker_combo_list" required=False, help="A list of the combination "
                        + "markers that should have calculations tabulated."
    parser.add_argument("-a", "--age_groups", required=False, help="A comma-delimited list of optional "
                        + "age groups that results can be categorized under")
    parser.add_argument("-c", "--copy_number_groups", required=False, help="A list of groups that copy "
                        + "number data should be binned into.")
    parser.add_argument('-q', "--query_params", required=False, help="The WHERE clause in our query "
                        + "statement emulating the behavior of our future CGI script"
    parser.add_argument("-o", "--output_file", required=True, help="Desired output file containing "
                        + "WWARN calculations.")
 
    args = parser.parse_args()
    return args

def parseMarkerList(markerList):
    """
    Parse the passed in marker list to produce a dictionary that can be used to 
    look up all valid genotypes for a given marker (or marker combination) as 
    well as an optional abbrevation for our marker. The marker list should
    be in the following format:

    #MARKER_NAME  LOCUS_POSITION  MARKER TYPE  VALID GENOTYPES
       pfcrt           76             SNP      K:Wild,T:Pure,K/T:Mixed    

    The VALID GENOTYPES column contains the valid genotypes we should see for a 
    given marker as well as a label that should be used in the output table.
    """
    markerLookup = {}
    
    markerListFH = open(markerList)
    for line in markerListFH:
        if line.startswith('#'):
            continue

        # TODO: Work in code to handle any combination markers        
        (markerName, locusPos, _markerType, markerAbbrev, genotypes) = line.rstrip('\n').split('\t')
        markerLookup.setdefault((markerName, locusPos), {})['abbrev'] = markerAbbrev
        markerLookup[(markerName, locusPos)].setdefault('genotypes', []) = list(parseGenotypesList(genotypes))
        
    return markerLookup        

def parseGenotypesList(genotypes):
    """
    Parses our genotype list returning a tuple of (value, label) from a 
    comma-delimited string formatted like so:

        VALUE:LABEL,VALUE:LABEL,.....
    
    Returns a generator that yields the tuple described above
    """        
    for genotype in genotypes.split(','):
        value = ""
        label = ""

        if genotype and genotype.find(':'):
            (value, label) = genotype.split(':', 1)
        elif genotype:
            value = genotype
        else                            
            raise Exception("Empty genotype found in valid genotypes list: %s - %s" % 
                            (markerName, locusPos)
        
        yield (value, label)                            
            
def main(parser):
    wwarnCalcDict = OrderedDict()

    # Parse our age and copy number groups to allow us to further group 
    # our results
    ageGroups = parseAgeGroups(parser.age_groups)
    copyNumberGroups = parseCopyNumberGroups(parser.copy_number_groups)

    # Parse our marker list to create a map that will aid us in printing our
    # output table.
    markerMap = parseMarkerList(parser.marker_list)

    # Now we can move onto generating our calculations
    calculateWWARNStatistics(wwarnCalcDict, createMySqlIterator(p

if __name__ == "__main__":
    main(buildArgParser())


