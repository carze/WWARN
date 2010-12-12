#!/usr/bin/python

__author__ = "Cesar Arze"
__version__ = "0.1-dev"
__maintainer__ = "Cesar Arze"
__email__ = "carze@som.umaryland.edu"
__status__ = "Development"

##
# This library performs the necessary WWARN calculations to produce both prevalence 
# and total genotyped statistics

def calculateWWARNStatistics(state, data, markerList=None):
    """
    Calculates the sample size and prevalence statistics for the data
    source passed in. Returned in a dictionary built in the following 
    format:

        { (STUDY_ID, COUNTRY, SITE, INVESTIGATOR, PATIENT_ID): {
            (LOCUS_NAME, LOCUS_POSITION): {
                'sample_size': <SAMPLE SIZE>
                MAKRER_VALUE: {
                    <VALUE>: <COUNT> } } }
    """
    # Tabulate our sample size and marker counts
    tabulateMarkerCounts(state, data, markerList)
    
    # Calculate prevalence
    calculatePrevalenceStatistic(state)

    print state

def tabulateMarkerCounts(state, data, markerList=None):
    """
    This function iterates over the source of data and updates
    a state variable used to keep track of the current sample 
    size and total genotyped counts for a given marker or set
    of markers
    """
    # Loop over each line of our input and pull out all the information we are
    # going to need to take accurate sample size and genotyped counts
    for line in data:
        studyLabel = line[0]
        investigator = line[1]
        country = line[2]
        site = line[3]
        age = line[4]

        # Split out our marker name + type combination and the genotype value 
        # from our last list element
        markersKey = parseMarkerComponents(line[5])
        genotypesKey = parseGenotypeValues(line[6])

        # Increment count for this marker
        incrementGenotypeCount(state, (studyLabel, country, site, investigator), markersKey, genotypesKey)

def parseMarkerComponents(rawMarkerStr):
    """
    Parses the raw marker string passed in as input to the calculations library
    and returns a tuple of tuples containing locus name and position for as many
    markers are present in this line of input
    """
    markerList = []
    
    # Our markers will come in the format of <LOCUS NAME>_<LOCUS POS>_<GENOTYPE VAUE> 
    # (e.x. pfcrt_76_A or pfdhps_540_E + pfdhps_437G)
    if rawMarkerStr.find('+') != -1:
        # We are dealing with a marker combination here
        markers = rawMarkerStr.split(' + ')
    else:
        markers = [rawMarkerStr]

    for marker in markers:
        (locusName, locusPos, markerType) = marker.split('_')
        markerList.extend( [locusName, locusPos] )
    
    return tuple(markerList)

def parseGenotypeValues(genotypeStr):
    """
    Parses the genotype(s) provided in the input file. Genotypes
    can be one or many values that are delimited by a '+'. Only in
    combinations should multiple genotype values be provided. 
    """
    genotypeList = []

    # If this genotype call corresponds with a marker combination 
    # it should be in the format of <GENOTYPE1> + <GENOTYPE2> + ... + <GENOTYPEN>
    if genotypeStr.find(' + ') != -1:
        genotypes = genotypeStr.split(' + ')
    else:
        genotypes = [genotypeStr]

    genotypeList.extend(genotypes)
    
    return tuple(genotypeList)

def incrementGenotypeCount(dict, metaKey, markerKey, genotype):
    """
    Increment the state dictionary with the three keys provided. If the key does
    not already exist in the dictionary the default value is set to 1 otherwise
    it is incremented by 1
    """
    # Check if our keys have already been initialized in our dictionary and if 
    # not we want to do so and return 0
    v = dict.setdefault(metaKey, {}).setdefault(markerKey, {}).setdefault(genotype, {}).get('genotyped', 0)
    v += 1

    # Now do the same for the sample size
    s = dict.setdefault(metaKey, {}).setdefault(markerKey, {}).get('sample_size', 0)
    s += 1

    dict[metaKey][markerKey]['sample_size'] = s
    dict[metaKey][markerKey][genotype]['genotyped'] = v


def calculatePrevalenceStatistic(data):
    """
    Iterate over a state variable that has been created via the tabulateMarkerCounts 
    function. This will perform the necessary calculations to populate the state
    variable with a prevalence statistic

    Prevalence can be calculated by taking the total genotyped/CN and dividing it by 
    the sample size of the marker
    """    
    # Need to loop over the dictionary and do our calculations
    for dataElemList in generateCountList(data):
        sampleSize = dataElemList[2]
        markerGenotyped = dataElemList[4]
        markerPrevalence = float(markerGenotyped) / sampleSize

        data[ dataElemList[0] ][ dataElemList[1] ][ dataElemList[3] ]['prevalence'] = markerPrevalence 

def generateCountList(data):    
    """
    This function is a generator function that returns a list of all the elements in 
    our state dictionary to allow for easier calculations. The list is structured to allow 
    us to do our calculations and easily add it back in place into the state variable:

    [ (STUDY_LABEL, COUNTRY, SITE, INVESTIGATOR, PATIENT_ID), (LOCUS_NAME, LOCUS_POS), SAMPLE_SIZE, MARKER_VALUE, COUNT)
    """     
    for outerTupleKey in data:
        for locusTuple in data[outerTupleKey]:
            # Get sample size
            sampleSize = data[outerTupleKey][locusTuple]['sample_size']

            for markerValue in data[outerTupleKey][locusTuple]:
                # Hacky but we need to make sure to skip sample size if 
                # we run into it.
                if markerValue == 'sample_size':
                    continue
                
                markerCount = data[outerTupleKey][locusTuple][markerValue]['genotyped']
                dataPrevList = [outerTupleKey, locusTuple, sampleSize, markerValue, markerCount]
                yield dataPrevList
