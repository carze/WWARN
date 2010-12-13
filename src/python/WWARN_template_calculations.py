###
# This script executes the WWARN calculations using the tab-delimited text file
# produced by the WWARN template as input data.

import argparse
import re

from wwarnCalculations import calculateWWARNStatistics
from string import strip

# A white list of columns that we want to capture and pass into our calculations
# code
META_COL = ['STUDY_LABEL', 'INVESTIGATOR', 'COUNTRY', 'SITE', 'AGE', 'PATIENT_ID']

def buildArgParser():
    """
    Creates an argparser object using the command-line arguments passed into this script
    """
    parser = argparse.ArgumentParser(description='Produces sample size and prevalence calculations '
                                        + 'given data provided from the WWARN database')
    parser.add_argument('-i', '--input_file', required=True, help='The tab-delimited text file produced from the '
                            + 'TEMPLATE worksheet in the WWARN Template')
    parser.add_argument('-m', '--marker_list', required=False, help='A list of all possible markers that should be '
                            + 'looked at in tabulating these statistics.')
    parser.add_argument('-a', '--age_groups', required=False, help='A comma-delimited list of optional age groups '
                            + 'that results should also be categorized under.')
    parser.add_argument('-o', '--output_file', required=True, help='Desired output file containing WWARN calculations.')
    args = parser.parse_args()

    return args

def parseAgeGroups(groups):
    """
    Returns a list of age groups to bin our statistics calculations. Input must be a 
    comma-delimited list in the following format:

        None-1, 1-4, 5-6, 12-None
    
    Encountering 'None' in a range can either be interpreted (using the examples above)
    as < 1 and > 12
    """
    ageList = []

    groups = ''.join( groups.split() )  # Strip any white space
    for ageRange in [x for x in groups.split(',')]:
        (lower, upper) = ageRange.split('-')

        # Cast our variables to float if they are not 'None'
        # And None if they are 'None'
        if lower == 'None':
            lower = None
            upper = float(upper)
        elif upper == 'None':
            upper = None
            lower = float(lower)
        else:
            lower = float(lower)
            upper = float(upper)

        ageList.append( (lower, upper) )

    return ageList

def createFileIterator(inputFile):
    """
    Takes an input file and creates a generateor of said file returning
    a line in dictionary form (with headers as k-v pairs)
    """
    wwarnFH = open(inputFile)

    # Assuming the first line is the header, very dangerous assumption     
    wwarnHeader = wwarnFH.readline().rstrip('\n').split('\t')   
    
    # To the genearting!
    # TODO: Fix up this ugly hack perhaps using some python tricks
    for row in wwarnFH:
        rowMeta = [v for (k,v) in zip(wwarnHeader, row.rstrip('\n').split('\t')) if k in META_COL]

        # Now add both our marker name and genotype value to the list
        # We can do this by iterating over row elements 9 and over as these 
        # are guaranteed to be our markers
        dataElems = row.rstrip('\n').split('\t')

        # Instead of looping over the number of elements in the dataElems list we 
        # want to loop over the header to make sure we don't try to pull in any extra
        # blank spaces at the end of the line
        for i in range(9, len(wwarnHeader)):
            print "%r: %r" % (rowMeta[5], row)
            rowList = rowMeta + [ wwarnHeader[i], dataElems[i] ]
            yield rowList

def createOutputWWARNTables(data, output):
    """
    Writes WWARN output tables for sample size and prevalence statistics
    in the following format:

    Output should be printed in the following manner:
       
     SITE   | SAMPLE SIZE | GENOTYPE 1 | GENOTYPE 2 | ... | GENOTYPE N |
     -------------------------------------------------------------------
     SITE 1 |     X       | PREVALENCE | PREVALENCE | ... | PREVALENCE |
       .
       .
       .   

    Each marker should have its own unique table created
    """
    wwarnOut = open(output, 'w')
    
    for markersDict in generateOutputDict(data):
        for site in markersDict:
            pass

def generateOutputDict(data):
    """
    Generates a more friendly output data structure to iterate over when printout 
    out the sample size and prevalence tables for the WWARN contributor report
    """
    pass

def main(parser):
    # Our state variable
    wwarnDataDict = {}
    
    # If the age groups parameter is used we want to parse it
    ageGroups = parseAgeGroups(parser.age_groups)

    # We can invoke the calculations library by passing in an iterator that iterates over 
    # our file and returns a dictionary containing all the information we need. Alongside 
    # this a dictionary where results should be written to is also passed in
    calculateWWARNStatistics(wwarnDataDict, createFileIterator(parser.input_file), parser.marker_list, ageGroups)
    
    # Finally print the statistics to the desired output file
    #createOutputWWARNTables(wwarnDataDict, parser.output_file)

if __name__ == "__main__":
    main(buildArgParser())        

