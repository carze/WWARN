###
# This script executes the WWARN calculations using the tab-delimited text file
# produced by the WWARN template as input data.

import argparse

from wwarnCalculations import tabulateMarkerCounts, calculatePrevalenceStatistic, calculateWWARNStatistics

# This is a whitelist of columns of metadata we want to include in the dictionaries we 
# yield to the calculations code
META_COL = ['STUDY_LABEL', 'PATIENT_ID', 'COUNTRY', 'SITE', 'INVESTIGATOR', 'AGE']

# When we are generating our dictionary row representation we want to skip
# adding these columns to the dict
SKIP_COL = ['STUDY_ID', 'DATE_OF_INCLUSION', 'SAMPLE_COLLECTION_DATE']

def buildArgParser():
    """
    Creates an argparser object using the command-line arguments passed into this script
    """
    parser = argparse.ArgumentParser(description='Produces sample size and prevalence calculations '
                                        + 'given data provided from the WWARN database')
    parser.add_argument('-i', '--input_file', help='The tab-delimited text file produced from the '
                            + 'TEMPLATE worksheet in the WWARN Template')
    parser.add_argument('-m', '--marker_list', help='A list of all possible markers that should be '
                            + 'looked at in tabulating these statistics.')
    parser.add_argument('-o', '--output_file', help='Desired output file containing WWARN calculations.')
    args = parser.parse_args()

    return args

def createFileIterator(inputFile):
    """
    Takes an input file and creates a generateor of said file returning
    a line in dictionary form (with headers as k-v pairs)
    """
    wwarnFH = open(inputFile)

    # Assuming the first line is the header, very dangerous assumption     
    wwarnHeader = wwarnFH.readline().rstrip('\n').split('\t')   
    
    # To the genearting!
    for row in wwarnFH:
        # Each yield should produce a dictionary with the follwing information
        # { STUDY_LABEL, INVESTIGATOR, COUNTRY, SITE, PATIENT_ID, AGE, MARKER_NAME, GENOTYPE VALUE }
        dictRow = dict( (k,v) for (k,v) in zip(wwarnHeader, row.rstrip('\n').split('\t')) if k in META_COL )
        yield dictRow

def main(parser):
    # Our state variable
    wwarnDataDict = {}

    # We can invoke the calculations library by passing in an iterator that iterates over 
    # our file and returns a dictionary containing all the information we need. Alongside 
    # this a dictionary where results should be written to is also passed in
    calculateWWARNStatistics(wwarnDataDict, createFileIterator(parser.input_file), parser.marker_list)
    
    # Handle output here yo!
    # Now we want to print our output in a tab-delimited format that 
    
if __name__ == "__main__":
    main(buildArgParser())        

