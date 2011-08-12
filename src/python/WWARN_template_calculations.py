###
# This script executes the WWARN calculations using the tab-delimited text file
# produced by the WWARN template as input data.

import argparse
import ConfigParser

from wwarncalculations import calculateWWARNStatistics
from wwarnexceptions import AgeGroupException, CopyNumberGroupException
from collections import OrderedDict
from wwarnutils import (validateGenotypes, create_year_bins, pprint,
                        get_template_date_bounds, parse_site, commaDelimToTuple)
from datetime import datetime

# A white list of columns that we want to capture and pass into our calculations
# code
META_COL = ['STUDY_ID', 'STUDY_LABEL', 'INVESTIGATOR', 'COUNTRY', 'SITE', 'AGE', 'PATIENT_ID', 'DATE_OF_INCLUSION']

def buildArgParser():
    """
    Creates an argparser object using the command-line arguments passed into this script
    """
    parser = argparse.ArgumentParser(description='Produces sample size and prevalence calculations '
                                        + 'given data provided from the WWARN database')
    parser.add_argument('-i', '--input_file', required=True, help='The tab-delimited text file produced from the '
                            + 'TEMPLATE worksheet in the WWARN Template')
    parser.add_argument('-c', '--config_file', required=True, help='A configuration file containing parameters '
                            + 'required for execution of the calculations script.')
    parser.add_argument('-m', '--marker_list', required=False, help='A list of all possible markers that should be '
                            + 'looked at in tabulating these statistics.')
    parser.add_argument("-b", "--bin-by-year", required=False, help="Bin all studies by a year range. " 
                            + "This year range should be defined in a digit representing the number of years " 
                                                    + "to create bins with (i.e. 1 = 1 year = 365 days)", type=int, dest="year_step")
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
    Parses the list of valid genotypes for a given marker and returns
    a dictionary that can be used to look up all of these genotypes. 
    This dictionary also contains a lookup table for our combination
    markers to provide abbreviated names when generating table output
    """
    markerMap = OrderedDict()

    genotypeListFH = open(markerListFile)
    for line in genotypeListFH:
        if line.startswith('#'):
            continue
            
        elts = line.strip().split('\t')            
        names = commaDelimToTuple(elts[0])
        positions = commaDelimToTuple(elts[1])
        genotypes = commaDelimToTuple(elts[3])
        
        # We want to create a tuple combining our marker names + positions 
        # to mainly represent occurances of our combination markers
        markerPosTuple = tuple(zip(names, positions))
        markerMap.setdefault(markerPosTuple, OrderedDict())
        markerMap.get(markerPosTuple).setdefault('valid', [])

        # If we have more than one marker name in our tuple we are dealing
        # with a combination marker
        if len(names) > 1:
            category = elts[4]
            label = elts[5]

            if not label in markerMap.get(markerPosTuple).get('valid'):
                markerMap.get(markerPosTuple).get('valid').append(label)    

            markerMap.get(markerPosTuple).setdefault(genotypes, OrderedDict())
            markerMap[markerPosTuple]['category'] = category
            markerMap[markerPosTuple][genotypes]['label'] = label
        else:
            markerMap.get(markerPosTuple).get('valid').extend(elts[3].split(','))    

    genotypeListFH.close()
    return markerMap

def createFileIterator(inputFile, cnBins, markerMap, year_step):
    """
    Takes an input file and creates a generateor of said file returning
    a line in dictionary form (with headers as k-v pairs)
    """
    wwarnFH = open(inputFile)

    # If we have metadata provided here we'll want to parse it out
    header_line = wwarnFH.readline()
    if header_line.startswith('#METADATA'):
        metadata = parse_metadata_header(header_line)
        year_step = metadata.get('year_step')
        header_line = wwarnFH.readline()

    wwarnHeader = [k for k in header_line.replace('#', '').rstrip('\n').split('\t') if len(k) != 0]   
    
    # If we are also binning by year we are going to want to create our bins 
    # prior to parsing all of the data
    if year_step:
        bounds = get_template_date_bounds(wwarnFH)
        year_bins = create_year_bins(year_step, bounds)

    for row in wwarnFH:
        if all(s == '\t' for s in row.rstrip('\r\n')) or row.startswith('#'):
            continue
    
        rowMeta = [v for (k,v) in zip(wwarnHeader, row.rstrip('\n').split('\t')) if k in META_COL]

        # If we are binning by years we'll need to modify our site to include the year range.
        rowMeta[-1] = datetime.strptime(rowMeta[-1], '%Y-%m-%d')
        rowMeta[4] = parse_site(rowMeta[4], rowMeta[2], rowMeta[-1], year_bins)
        del rowMeta[-1] # Remove the DOI when we are done with it

        dataElems = row.rstrip('\n').split('\t')
        
        # Instead of looping over the number of elements in the dataElems list we 
        # want to loop over the header to make sure we don't try to pull in any extra
        # blank spaces at the end of the line
        markerData = zip(wwarnHeader[9:], dataElems[9:])

        # Get our combination markers data
        combinationMarkers = getCombinationMarkers(dict(markerData),
                       [k for k in markerMap.keys() if len(k) >= 2])
        markerData = markerData + combinationMarkers

        for (marker, genotype) in markerData:
            if len(genotype) == 0: continue

            # We want to check to see if we are dealing with a marker of type copy number
            # (and in the future genotype fragment) and handle these accordingly
            if marker.find('CN') != -1 and validateGenotypes([genotype]):
                # We are dealing with a marker of type copy number and must pre-bin this 
                # value into one of the categories provided via command line
                genotype = preBinCopyNumberData(genotype, cnBins)

            rowList = rowMeta + [ marker, genotype.strip() ]
            yield rowList

def getCombinationMarkers(markerData, comboLookup):
    """
    Examines a row of markers/genotypes from the data file and identifies
    all combination markers that exist in the current row of data.
    """
    comboMarkerData = []
        
    # Convert the list of of markers into         
    inputMarkerSet = set(([tuple(z.replace('_SNP_AA', '',).split('_')) for z in markerData.keys()]))
           
    for comboMarker in comboLookup:
        comboSet = set(comboMarker)

        if comboSet.issubset(inputMarkerSet):
            # We now know that this combination marker exists in our data set
            # so we need to add it to our marker data list
            markers = []
            genotypes = []
            for (marker, pos) in comboMarker:
                markerStr = "%s_%s_SNP_AA" % (marker, pos)
                markers.append(markerStr)
                genotypes.append(markerData.get(markerStr))

            comboMarkerData.append((" + ".join(markers), " + ".join(genotypes)))                
    
    return comboMarkerData                
               
def parse_metadata_header(metadata_header):
    """
    Parses any metadata in the header of a WWARN template file. This metadata
    is defined by a #METADATA line:

        #METADATA:year_step=1

    A dictionary will be created out of the k=v pairs found in the header line        
    """
    metadata_dict = OrderedDict()
    metadata_elts = (metadata_header.rstrip('\n').split(':'))[1].split(',')

    for (k, v) in [x.split('=') for x in metadata_elts]:
        metadata_dict[k] = int(v)

    return metadata_dict

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
    
    # We need to grab (and sort) all the genotypes we will be dealing with
    # for this input file
    for outDict in generateOutputDict(data, genotypeList):
        for (locusTuple, siteIter) in outDict.iteritems():
            # Check if we are dealing with a combination marker first
            header = []
            if len(locusTuple) > 1:
                header = getValidComboMarkers(locusTuple, genotypeList)
                header.extend(['Not Genotyped', 'Genotyping Failure'])
                locusTuple = getPrettyComboMarkerLabel(locusTuple, genotypeList)
            else:
                header = genotypeList[locusTuple].get('valid')

            wwarnOut.write( " ".join(locusTuple[0]) + "\n" )
            wwarnOut.write( "Site\tAge group\tSample size\t%s\n" % "\t".join(["%s" % e for e in header]) )

            for (site, groupsIter) in siteIter.iteritems():
                wwarnOut.write("%s" % site)
                
                for (group, genotypesIter) in groupsIter.iteritems():
                    if groupsIter[group]['sample_size'] == 0:
                        continue

                    wwarnOut.write("\t%s\t%s" % (group, groupsIter[group]['sample_size']))

                    for genotype in header:
                        statistic = genotypesIter.get(tuple(genotype), 0)

                        # When dealing with our mixed genotypes we must make sure to check both 
                        # the A/B combination and the B/A combination
                        if statistic == 0 and genotype[0].find('/') != -1:
                            statistic = genotypesIter.get(tuple(genotype[::-1]), 0)

                        if validateGenotypes([genotype]):
                            statistic = "{0:.0%}".format(statistic)

                        wwarnOut.write("\t%s" % (statistic))

                    wwarnOut.write("\n")
            wwarnOut.write("\n")

def getPrettyComboMarkerLabel(comboMarker, markerMap):
    """
    Retrieves the pretty name for our combo markers (i.e. pfdhps 540 + 
    pfdhps 437 -->  pfdhps double)
    """       
    prettyName = None

    inputMarkerSet = set(comboMarker)
    for combo in [x for x in markerMap.keys() if len(x) > 1]:
        comboSet = set(combo)

        if inputMarkerSet.issubset(comboSet):
            prettyName = markerMap.get(combo).get('category')
            break

    return [(prettyName,)]

def getValidComboMarkers(comboMarker, markerMap):
    """
    Retrieves the valid combo marker genotypes. This is done by checking the 
    marker map against the passed in marker using set operations
    """
    validGenotypes = []

    inputMarkerSet = set(comboMarker)
    for combo in [x for x in markerMap.keys() if len(x) > 1]:
        comboSet = set(combo)

        if inputMarkerSet.issubset(comboSet):
            validGenotypes = markerMap.get(combo).get('valid')
            break

    return validGenotypes           

def generateOutputDict(data, map):
    """
    Generates a more "friendly" output data structure to iterate over when printout 
    out the sample size and prevalence tables for the WWARN contributor report.
    Format for returned dictionary is below:
    
      {  <MARKER NAME>: {
          <SITE>: {
              <GROUP>: { [SAMPLE_SIZE, PREVALENCE VALUES.... ]
    """
    outputDict = OrderedDict()
    prevSite = None
    
    for (metadataKey, locusIter) in data.iteritems():
        site = metadataKey[3]
        if prevSite is not None and site != prevSite:
            yield outputDict
            outputDict = OrderedDict()
            prevSite = site
        
        for (markerKey, genotypesIter) in locusIter.iteritems():
            outputDict.setdefault(markerKey, OrderedDict()).setdefault(site, OrderedDict())

            for genotype in genotypesIter:
                sortedGroups = genotypesIter[genotype].keys()
             
                # If we are working with a combination marker we will want to 
                # use our 'pretty' name for our genotypes
                label = None
                if len(markerKey) > 1:
                    label = getComboMarkerLabel(map.get(markerKey), genotype)
                                  
                for group in sortedGroups:
                    outputDict[markerKey][site].setdefault(group, OrderedDict())

                    if genotype == 'sample_size':
                        sampleSize = locusIter[markerKey]['sample_size'][group]
                        outputDict[markerKey][site][group]['sample_size'] = sampleSize
                    else:                         
                        #outputDict[markerKey][site][group].setdefault(genotype, OrderedDict())

                        # If our 'genotype' is Not genotyped or Genotyping failure we 
                        # want to get the number of occurances of these instead of the prevalence
                        if validateGenotypes(list(genotype)):
                            prevalence = genotypesIter[genotype][group]['prevalence']
                            
                            if label:
                                outputDict.get(markerKey).get(site).get(group).setdefault(label, 0)
                                outputDict[markerKey][site][group][label] += prevalence
                            else:                                
                                outputDict.get(markerKey).get(site).get(group).setdefault(genotype, 0)
                                outputDict[markerKey][site][group][genotype] += prevalence

                        else:                            
                            genotypeCount = genotypesIter[genotype][group]['genotyped']

                            if label:
                                outputDict[markerKey][site][group].setdefault(label, 0)
                                outputDict[markerKey][site][group][label] += genotypeCount
                            else:
                                outputDict[markerKey][site][group].setdefault(genotype, 0)
                                outputDict[markerKey][site][group][genotype] += genotypeCount

    yield outputDict

def getComboMarkerLabel(map, genotype):
    """
    Retrieves the label for a given combination marker. Because the ordering
    of markers within a combination can be different we must convert everything
    to sets to check whether or not we have a match
    """
    label = None

    for (comboMarker, metadata) in map.items(): 
        if comboMarker == 'valid':
            continue

        comboSet = set(comboMarker)
        genotypeSet = set(genotype)
        
        if comboSet.issubset(genotypeSet):
            label = tuple(metadata.get('label'))
            
    return label                                      

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
    wwarnDataDict = OrderedDict()
  
    config = ConfigParser.RawConfigParser()
    config.read(parser.config_file)
    ageGroups = parseAgeGroups(config.get('GENERAL', 'age_groups'))
    copyNumGroups = parseCopyNumberGroups(config.get('GENERAL', 'copy_number_groups'))
    markerMap = parseMarkerList(parser.marker_list)

    calculateWWARNStatistics(wwarnDataDict, createFileIterator(parser.input_file, copyNumGroups, markerMap, parser.year_step), ageGroups)
    createOutputWWARNTables(wwarnDataDict, markerMap, parser.output_file)

if __name__ == "__main__":
    main(buildArgParser())        

