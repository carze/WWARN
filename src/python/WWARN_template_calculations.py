###
# This script executes the WWARN calculations using the tab-delimited text file
# produced by the WWARN template as input data.

import argparse

from wwarncalculations import calculateWWARNStatistics
from wwarnexceptions import AgeGroupException, CopyNumberGroupException
from pprint import pprint

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
    parser.add_argument('-c', '--copy_number_groups', required=False, help='A list of groups that copy numberd data '
                            + 'should be binned into.')
    parser.add_argument('-o', '--output_file', required=True, help='Desired output file containing WWARN calculations.')
    args = parser.parse_args()

    return args

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

def parseMarkerList(markerListFile):
    """
    Parses the optional list of valid genotypes for a given marker and returns
    a dictionary that can be used to look up all of these genotypes. This is useful
    if we want to see which genotypes were not genotyped in a set of data
    """
    validGenotypes = {}

    # Open file and grab all genotypes (comma-delimited list) to be placed
    # in our dictionary
    genotypeListFH = open(markerListFile)
    for line in genotypeListFH:
        (marker, genotypes) = line.rstrip('\n').split('\t')

        validGenotypes[marker] = [(x,) for x in genotypes.split(',')]

    return validGenotypes

def createFileIterator(inputFile, cnBins):
    """
    Takes an input file and creates a generateor of said file returning
    a line in dictionary form (with headers as k-v pairs)
    """
    wwarnFH = open(inputFile)

    # Assuming the first line is the header, very dangerous assumption     
    wwarnHeader = [k for k in wwarnFH.readline().rstrip('\n').split('\t') if len(k) != 0]   
    
    # To the genearting!
    # TODO: Fix up this ugly hack perhaps using some python tricks
    for row in wwarnFH:
        if all(s == '\t' for s in row.rstrip('\r\n')):
            continue

        rowMeta = [v for (k,v) in zip(wwarnHeader, row.rstrip('\n').split('\t')) if k in META_COL]

        # Now add both our marker name and genotype value to the list
        # We can do this by iterating over row elements 9 and over as these 
        # are guaranteed to be our markers
        dataElems = row.rstrip('\n').split('\t')
        
        # Instead of looping over the number of elements in the dataElems list we 
        # want to loop over the header to make sure we don't try to pull in any extra
        # blank spaces at the end of the line
        for i in range(9, len(wwarnHeader)):
            marker = wwarnHeader[i]
            genotype = dataElems[i]

            # We want to check to see if we are dealing with a marker of type copy number
            # (and in the future genotype fragment) and handle these accordingly
            if marker.find('CN') != -1 and genotype not in ['Genotyping failure', 'Not genotyped']:
                # We are dealing with a marker of type copy number and must pre-bin this 
                # value into one of the categories provided via command line
                genotype = preBinCopyNumberData(genotype, cnBins)

            rowList = rowMeta + [ wwarnHeader[i], genotype ]
            yield rowList

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

def createOutputWWARNTables(data, genotypeList, output):
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
    
    # The data structure returned from the calculations script needs to be 
    # transformed into something that we can more easily work with to produce the 
    # output we need

    # We need to grab (and sort) all the genotypes we will be dealing with
    # for this input file
    for outDict in generateOutputDict(data):
        for (locusTuple, siteIter) in outDict.iteritems():
            # Print out our header here; we need one table per marker 
            # so we will be printing the header out multiple times
            markerName = locusTuple[0] + locusTuple[1]
            header = genotypeList[markerName]

            wwarnOut.write( "".join(locusTuple) + "\n" )
            wwarnOut.write( "Site\tAge group\tSample size\t%s\n" % "\t".join(["%s" % e for e in header]) )

            # Iterate over each site and write out the corresponding sample size + prevalence values
            for (site, groupsIter) in siteIter.iteritems():
                wwarnOut.write("%s" % site)
                
                for (group, genotypesIter) in groupsIter.iteritems():
                    wwarnOut.write("\t%s\t%s" % (group, groupsIter[group]['sample_size']))

                    for genotype in header:
                        # Hacky but we need to replace No data and Null with their correct
                        # representations in our template.
                        if genotype[0] == 'No data':
                            genotype = ('Not genotyped',)
                        elif genotype[0] == 'Null':
                            genotype = ('Genotyping failure',)
                                                        
                        statistic = genotypesIter.get(genotype, 0)

                        # When dealing with our mixed genotypes we must make sure to check both 
                        # the A/B combination and the B/A combination
                        if statistic == 0 and genotype[0].find('/') != -1:
                            # We are dealing with a mixed genotype here and need to try both
                            # combinations - A/B and B/A 
                            statistic = genotypesIter.get(genotype[::-1], 0)

                        if genotype[0] not in ['Not genotyped', 'Genotyping failure']:
                            statistic = "%5.1f%%" % (100 * statistic)

                        wwarnOut.write("\t%s" % (statistic))

                    print wwarnOut.write("\n")

        print wwarnOut.write("\n\n")                    

def generateOutputDict(data):
    """
    Generates a more "friendly" output data structure to iterate over when printout 
    out the sample size and prevalence tables for the WWARN contributor report.
    Format for returned dictionary is below:
    
      {  <MARKER NAME>: {
          <SITE>: {
              <GROUP>: { [SAMPLE_SIZE, PREVALENCE VALUES.... ]
    """
    outputDict = {}
    prevSite = None

    for (metadataKey, locusIter) in data.iteritems():
        # We need to pull out site from here to be used as one our keys
        site = metadataKey[2]
        if prevSite is not None and site != prevSite:
            yield outputDict
            outputDict = {}
            prevSite = site
        
        # We also need a list of of our sorted genotypes that will be used
        # to generate our table header
        for (markerKey, genotypesIter) in locusIter.iteritems():
            outputDict.setdefault(markerKey, {}).setdefault(site, {})
        
            # Now loop over all our genotypes and grab all the prevalences 
            # to go alongside our sample sizes
            for genotype in genotypesIter:
                sortedGroups = sorted( genotypesIter[genotype].keys() )
               
                for group in sortedGroups:
                    outputDict[markerKey][site].setdefault(group, {})

                    if genotype == 'sample_size':
                        sampleSize = locusIter[markerKey]['sample_size'][group]
                        outputDict[markerKey][site][group]['sample_size'] = sampleSize
                    else:                         
                        outputDict[markerKey][site][group].setdefault(genotype, {})

                        # If our 'genotype' is Not genotyped or Genotyping failure we 
                        # want to get the number of occurances of these instead of the prevalence
                        if genotype[0] in ['Not genotyped', 'Genotyping failure']:
                            genotypeCount = genotypesIter[genotype][group]['genotyped']
                            outputDict[markerKey][site][group][genotype] = genotypeCount
                        else:                            
                            prevalence = genotypesIter[genotype][group]['prevalence']
                            outputDict[markerKey][site][group][genotype] = prevalence

    yield outputDict

def parseHeaderList(headerList):
    """
    Parse the list of headers provided in the dictionary containing 
    our results. We want to convert any markers from tuple format to 
    a (list of) strings
    """
    headerStrList = []

    for headerTuple in headerList:
        # If our tuple is greater than size 1 we are dealing with 
        # combination markers and need to join them into one string with 
        # '+' in between them
        if len(headerTuple) > 1:
            headerStrList.append( " + ".join(headerTuple) )
        else:
            headerStrList.append( "".join(headerTuple) )

    return headerStrList

def main(parser):
    # Our state variable
    wwarnDataDict = {}
    
    # If the age groups parameter is used we want to parse it.
    # Likewise if we have a marker list we want to create a list of all possible
    # genotypes
    ageGroups = parseAgeGroups(parser.age_groups)
    copyNumGroups = parseCopyNumberGroups(parser.copy_number_groups)
    markerGenotypes = parseMarkerList(parser.marker_list)

    # We can invoke the calculations library by passing in an iterator that iterates over 
    # our file and returns a dictionary containing all the information we need. Alongside 
    # this a dictionary where results should be written to is also passed in
    calculateWWARNStatistics(wwarnDataDict, createFileIterator(parser.input_file, copyNumGroups), ageGroups)
    
    pprint (wwarnDataDict, indent=2)

    # Finally print the statistics to the desired output file
    createOutputWWARNTables(wwarnDataDict, markerGenotypes, parser.output_file)

if __name__ == "__main__":
    main(buildArgParser())        

