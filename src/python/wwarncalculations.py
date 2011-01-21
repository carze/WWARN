#!/usr/bin/python

__author__ = "Cesar Arze"
__version__ = "1.0-dev"
__maintainer__ = "Cesar Arze"
__email__ = "carze@som.umaryland.edu"
__status__ = "Development"

##
# This library performs the necessary WWARN calculations to produce both prevalence 
# and total genotyped statistics

from collections import OrderedDict

def calculateWWARNStatistics(state, data, ageGroups=None):
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
    tabulateMarkerCounts(state, data, ageGroups)

    # Calculate prevalence
    calculatePrevalenceStatistic(state)

def tabulateMarkerCounts(state, data, ageGroups):
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
        age = line[5]

        # Our outer key in the calculations dictionary is a tuple containing 
        # some metadata: study label, country, site, investigator
        metadataKey = (studyLabel, country, site, investigator)

        # Check if our age is empty (empty string or NODATA) and if so set it
        # equal to None
        if age in ['', 'NODATA']:
            age = None

        # Split out our marker name + type combination and the genotype value 
        # from our last list element
        markersKey = parseMarkerComponents(line[6])
        genotypesKey = parseGenotypeValues(line[7]) 
        
        # Increment count for this marker
        incrementGenotypeCount(state, metadataKey, markersKey, genotypesKey, ageGroups, age)


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
        markerElems = marker.split('_')
        
        locusName = markerElems[0]
        # Only marker type SNP will carry a LOCUS_POS value
        if marker.find('CN') != -1 or marker.find('FRAG') != -1:
            locusPos = ''
        else:
            locusPos = markerElems[1]

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

def incrementGenotypeCount(dict, metaKey, markerKey, genotype, groups, age):
    """
    Increment the state dictionary with the three keys provided. If the key does
    not already exist in the dictionary the default value is set to 1 otherwise
    it is incremented by 1
    
    If a group of ages is passed into this function we also want to categorize 
    all of our increments 
    """
    # Check if our keys have already been initialized in our dictionary and if 
    # not we want to do so and return 0
    dict.setdefault(metaKey, OrderedDict()).setdefault(markerKey, OrderedDict()).setdefault(genotype, OrderedDict()).setdefault('All', OrderedDict()).setdefault('genotyped', 0)
    genotypeAll = dict[metaKey][markerKey][genotype]['All']['genotyped']
    genotypeAll += 1

    # Initialize our sample size to 0 to avoid any errors
    dict[metaKey][markerKey].setdefault('sample_size', OrderedDict()).setdefault('All', 0)

    # Now do the same for the sample size only if our 'genotype' is not 'No data' or 'Genotyping failure' -- these
    # two should not be counted towards the sample size.
    sampleAll = dict[metaKey][markerKey]['sample_size']['All']
    if genotype[0] not in ['Not genotyped', 'Genotyping failure']:
        sampleAll += 1
        dict[metaKey][markerKey]['sample_size']['All'] = sampleAll

    dict[metaKey][markerKey][genotype]['All']['genotyped'] = genotypeAll

    # If our age key is not None we need to add this age group
    if groups:
        incrementCountsByAgeGroup(dict, metaKey, markerKey, genotype, groups, age)

def incrementCountsByAgeGroup(dict, metaKey, markerKey, genotype, groups, age):
    """
    Initializes all age groups in our statistics dictionary and increments
    only the age groups where a row of data containing that age was found
    """
    groupKey = None

    for group in groups:
        # The groups list should contain a list of age groups in the following
        # tuple format:
        #
        #     [ (lower, upper, label), (lower, upper, label), .... ]
        #
        # We should always assume that our grouping will be lower <= age <= upper 
        # and our group key will be returned as "lower - upper".
        # 
        # The two fringe cases we will have to look out for will be (0, upper) 
        # and (lower, 200) in these cases we are dealing with edge cases such as   
        # (0, 1) and (12, 200) which would be represented as age < 1 and
        # age > 12
        #
        # The third element in the tuple, 'label', will represent the key assigned 
        #in the dictionary housing our statistics
        (lower, upper, label) = group   

        # First initialize this level of nesting in our dictionary if it hasn't 
        # already been initialized
        dict[metaKey][markerKey]['sample_size'].setdefault(label, 0)
        dict[metaKey][markerKey][genotype].setdefault(label, OrderedDict()).setdefault('genotyped', 0)

        # Now increment the correct category that the patient providing this 
        # data fell under
        if age is not None:
            if lower is None:
                if float(age) < upper:
                    groupKey = label
            
            if upper is None:
                if float(age) > lower:
                    groupKey = label

            if lower is not None and upper is not None:       
                if lower <= float(age) <= upper:
                    groupKey = label
     
    if groupKey is not None: 
        # Once again, hacky but we do not want to increment the sample size for a given
        # group if our genotype is 'Not genotyped' or 'Genotyping failure'
        if genotype[0] not in ['Not genotyped', 'Genotyping failure']:
            dict[metaKey][markerKey]['sample_size'][groupKey] += 1

        dict[metaKey][markerKey][genotype][groupKey]['genotyped'] += 1

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
        # If we are working with a 'genotype' or 'Genotyping failure' or 
        # 'No data' we want to skip prevalence calculations
        if (dataElemList[2])[0] in ['Genotyping failure', 'Not genotyped']: continue
        
        sampleSize = dataElemList[4]
        markerGenotyped = dataElemList[5]

        # If our genotyped count is 0 we want to set prevalence to 0 
        # to avoid division by zero
        markerPrevalence = 0
        if float(markerGenotyped) > 0:
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
