#!/usr/bin/python

__author__ = "Cesar Arze"
__version__ = "0.1-dev"
__maintainer__ = "Cesar Arze"
__email__ = "carze@som.umaryland.edu"
__status__ = "Development"

from AutoVivification import AutoVivification

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
    # Autovivify the dictionary so we don't have to worry about
    # declaring the nested levels
    state = AutoVivification()

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
        print line
        studyLabel = line[0]
        investigator = line[1]
        country = line[2]
        site = line[3]
        age = line[4]

        # Split out our marker name + type combination and the genotype value 
        # from our last list element
        print "DEBUG: %s" % line
        (markerTupleKey, genotypeVal) = parseMarkerComponents(line[5])
        
        # Increment count for this marker
        state[(studyLabel, country, site, investigator)][markerTupleKey][genotypeVal] += 1

def parseMarkerComponents(rawMarkerStr):
    """
    Parses the raw marker string passed in as input to the calculations library
    and returns a tuple of tuples containing locus name and position as well
    as the genotype value(s) for this marker or cominbation of markers

        i.e.
            ( (pfcrt, 76), 'K') 
            ( ((pfdhps, 540), (pfdhps, 437)), ['K', 'T'])
    """
    markerList = []
    genotypeValues = []

    # Our markers will come in the format of <LOCUS NAME>_<LOCUS POS>_<GENOTYPE VAUE> 
    # (e.x. pfcrt_76_A or pfdhps_540_E + pfdhps_437G)
    if rawMarkerStr.find('+') != -1:
        # We are dealing with a marker combination here
        markers = rawMarkerStr.split(' + ')
    else:
        markers = rawMarkerStr

    for marker in markers:
        (markerName, genotypeVal) = marker.split('_', 2)

        markerList.append(markerName)
        genotypeValues.append(genotypeVal)

    return ( tuple(markerList), tuple(genotypeValues) )

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
        # Pick up our sample size and genotyped count 
        # to do our calculation
        sampleSize = dataElemList[2]
        markerCount = dataElemList[4]
        markerPrevalence = markerCount / sampleSize
        
        data[ dataElemList[0] ][ dataElemList[1] ][ dataElemList[3] ]['prevalence'] = markerPrevalence 

def generateCountList(data):    
    """
    This function is a generator function that returns a list of all the elements in 
    our state dictionary to allow for easier calculations. The list is structured to allow 
    us to do our calculations and easily add it back in place into the state variable:

    [ (STUDY_LABEL, COUNTRY, SITE, INVESTIGATOR, PATIENT_ID), (LOCUS_NAME, LOCUS_POS), SAMPLE_SIZE, MARKER_VALUE, COUNT)
    """     
    dataPrevList = []

    for outerTupleKey in data:
        dataPrevList.append(outerTupleKey)

        for locusTuple in data[outerTupleKey]:
            dataPrevList.append(locusTuple)
            
            # Add sample size to the list
            sampleSize = data[outerTupleKey][locusTuple]['sample_size']
            dataPrevList.append(sampleSize)

            for markerValue in data[outerTupleKey][locusTuple]:
                # If we encounter our sample size we want to skip over it
                if markerValue == 'sample_size':
                    continue
                
                markerCount = data[outerTupleKey][locusTuple][markerValue]['count']
                dataPrevList.extend([markerValue, markerCount])

                yield dataPrevList
