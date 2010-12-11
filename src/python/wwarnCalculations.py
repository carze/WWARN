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
    # going to need to do our calculation
    for line in data:
        studyLabel = line.pop('STUDY_LABEL')
        investigator = line.pop('INVESTIGATOR') 
        country = line.pop('COUNTRY')
        site = line.pop('SITE')
        patientID = line.pop('PATIENT_ID')
        age = line.pop('AGE')

        ## TODO: This code currently does not handle marker combinations.

        # Now we need to update our state variable to add to its already existing counters
        # or add a new entry if it hasn't been seen already
        for marker in line:
            (locusName, locusPos, _discard) = marker.split('_')
            markerValue = line[marker]

            # Use setdefault to initialize our dictionary if the tuple keys we are 
            # about to add don't already exist
            initializeDefaults(state, studyLabel, country, site, investigator, locusName, locusPos, markerValue)
            
            state[(studyLabel, country, site, investigator)][(locusName, locusPos)]['sample_size'] += 1
            state[(studyLabel, country, site, investigator)][(locusName, locusPos)][markerValue]['count'] += 1

def initializeDefaults(state, study, country, site, investigator, name, position, value):
    """
    Initializes the nested structure of the state object to ensure that we do not run
    into a situation where we attempt to increment or add to an un-instantiated value
    """
    ## TODO: We will need to instantiate age groups here when they are implemented
    state.setdefault( (study, country, site, investigator), {} ).setdefault( (name, position), {})['sample_size'] = 0
    state.setdefault( (study, country, site, investigator), {} ).setdefault( (name, position), {}).setdefault(value, {})['count'] = 0

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
