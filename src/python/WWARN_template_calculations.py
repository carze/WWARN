###
# This script executes the WWARN calculations using the tab-delimited text file
# produced by the WWARN template as input data.

import argparse

from wwarnCalculations import calculateWWARNStatistics

# A blacklist of columns we do not want in our rowLists that are yielded to the calculations
# library
SKIP_COL = ['STUDY_ID', 'SAMPLE_COLLECTION_DATE', 'DATE_OF_INCLUSION', 'PATIENT_ID']

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
        yield [v for (k,v) in zip(wwarnHeader, row.rstrip().split('\t')) if k not in SKIP_COL]

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

