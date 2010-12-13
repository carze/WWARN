#!/usr/bin/python

__author__ = "Cesar Arze"
__version__ = "0.1-dev"
__maintainer__ = "Cesar Arze"
__email__ = "carze@som.umaryland.edu"
__status__ = "Development"

##
# This library performs the necessary WWARN calculations to produce both prevalence 
# and total genotyped statistics

from pprint import pprint

def calculateWWARNStatistics(state, data, markerList=None, ageGroups=None):
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
    tabulateMarkerCounts(state, data, markerList, ageGroups)
    
    # Calculate prevalence
   # calculatePrevalenceStatistic(state)

    pprint(state, indent=2)

def tabulateMarkerCounts(state, data, markerList, ageGroups):
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
        
        print "DEBUG: %s" % line

        # Split out our marker name + type combination and the genotype value 
        # from our last list element
        markersKey = parseMarkerComponents(line[6])
        genotypesKey = parseGenotypeValues(line[7])

        # If an age group is passed in we want to figure out what group this current line falls into
        if ageGroups and line[5]:
            age = float(line[5])
            ageKey = assignAgeGroup(ageGroups, age)
        else:
            ageKey = None

        # Increment count for this marker
        incrementGenotypeCount(state, (studyLabel, country, site, investigator), markersKey, genotypesKey, ageKey)

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

def assignAgeGroup(groups, age):
    """
    Places the age passed into the function into one of the groups 
    defined in the groups list. This list should contain a tuple of
    lower and upper bound ages that can be used to classify any age in the
    data set passed in
    """
    groupKey = ""

    for group in groups:
        # The groups list should contain a list of age groups in the following
        # tuple format:
        #
        #     [ (lower, upper), (lower, upper), .... ]
        #
        # We should always assume that our grouping will be lower <= age <= upper 
        # and our group key will be returned as "lower - upper".
        # 
        # The two fringe cases we will have to look out for will be (0, upper) 
        # and (lower, 200) in these cases we are dealing with edge cases such as   
        # (0, 1) and (12, 200) which would be represented as age < 1 and
        # age > 12
        (lower, upper) = group   

        if lower is None:
            if age < upper:
                groupKey = "< %s" % upper
                break
        
        if upper is None:
            if age > lower:
                groupKey = "> %s" % lower
                break
    
        if lower is not None and upper is not None:
            if lower <= age <= upper:
                groupKey = "%s - %s" % (lower, upper)
                break

    return groupKey

def incrementGenotypeCount(dict, metaKey, markerKey, genotype, ageKey):
    """
    Increment the state dictionary with the three keys provided. If the key does
    not already exist in the dictionary the default value is set to 1 otherwise
    it is incremented by 1
    
    If a group of ages is passed into this function we also want to categorize 
    all of our increments 
    """
    # Check if our keys have already been initialized in our dictionary and if 
    # not we want to do so and return 0
    genotypeAll = dict.setdefault(metaKey, {}).setdefault(markerKey, {}).setdefault(genotype, {}).setdefault('All', {}).get('genotyped', 0) 
    genotypeAll += 1

    # Now do the same for the sample size
    sampleAll = dict.setdefault(metaKey, {}).setdefault(markerKey, {}).setdefault('sample_size', {}).get('All', 0)
    sampleAll += 1

    dict[metaKey][markerKey]['sample_size']['All'] = sampleAll
    dict[metaKey][markerKey][genotype]['All']['genotyped'] = genotypeAll

    # If our age key is not None we need to add this age group
    if ageKey is not None:
        sampleAge = dict[metaKey][markerKey].setdefault('sample_size', {}).get(ageKey, 0)
        sampleAge += 1 
        dict[metaKey][markerKey]['sample_size'][ageKey] = sampleAge

        genotypeAge = dict[metaKey][markerKey][genotype].setdefault(ageKey, {}).get('genotyped', 0)
        genotypeAge += 1
        dict[metaKey][markerKey][genotype][ageKey]['genotyped'] = genotypeAge

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
        sampleSize = dataElemList[4]
        markerGenotyped = dataElemList[5]
        markerPrevalence = float(markerGenotyped) / sampleSize

        data[ dataElemList[0] ][ dataElemList[1] ][ dataElemList[2] ][ dataElemList[3] ]['prevalence'] = markerPrevalence 

def generateCountList(data):    
    """
    This function is a generator function that returns a list of all the elements in 
    our state dictionary to allow for easier calculations. The list is structured to allow 
    us to do our calculations and easily add it back in place into the state variable:

    [ (STUDY_LABEL, COUNTRY, SITE, INVESTIGATOR, PATIENT_ID), (LOCUS_NAME, LOCUS_POS), SAMPLE_SIZE, MARKER_VALUE, COUNT)
    """     
    for outerTupleKey in data:
        for locusTuple in data[outerTupleKey]:
            for genotype in [x for x in data[outerTupleKey][locusTuple] if x != "sample_size"]:
                for group in data[outerTupleKey][locusTuple][genotype]:
                    sampleSize = data[outerTupleKey][locusTuple]['sample_size'][group]
                    genotypedCount = data[outerTupleKey][locusTuple][genotype][group]['genotyped']
                    dataPrevList = [outerTupleKey, locusTuple, genotype, group, sampleSize, genotypedCount]
                    yield dataPrevList
