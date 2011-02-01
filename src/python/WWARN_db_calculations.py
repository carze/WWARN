#!/usr/bin/env python

##
# This script (soon to be CGI script) queries the back-end WWARN database to perform a 
# calculation on either a specific dataset pulled from the database (query with criteria)
# or the full set of data from the database.
#

import MySQLdb
import argparse
import ConfigParser

from collections import OrderedDict
from os.path import join
from itertools import chain
from wwarncalculations import calculateWWARNStatistics
from wwarnutils import parseAgeGroups, parseCopyNumberGroups, preBinCopyNumberData

def buildArgParser():
    """
    Builds an argparse object used to parse any command-line arguments passed
    into the script.
    """
    parser = argparse.ArgumentParser(description="Produces sample size and prevalence calculations "
                        + "given data provided from the WWARN database")
    parser.add_argument("-c", "--config_file", required=True, help="The datbase configuration file "
                        + "containing database login credentials")
    parser.add_argument("-m", "--marker_list", required=True, help="A list of all possible markers "
                        + "that should be present in our output")
    parser.add_argument("-mc" "--marker_combo_list", required=False, help="A list of the combination "
                        + "markers that should have calculations tabulated.")
    parser.add_argument("-a", "--age_groups", required=False, help="A comma-delimited list of optional "
                        + "age groups that results can be categorized under")
    parser.add_argument("-cn", "--copy_number_groups", required=False, help="A list of groups that copy "
                        + "number data should be binned into.")
    parser.add_argument('-q', "--query_params", required=False, help="The WHERE clause in our query "
                        + "statement emulating the behavior of our future CGI script")
    parser.add_argument("-o", "--output_directory", required=True, help="Desired output directory to write"
                        + " all calculations to.")
    parser.add_argument("-p", "--output_prefix", required=True, help="Desired output file prefix.")
 
    args = parser.parse_args()
    return args

def parseMarkerList(markerList):
    """
    Parses the passed in marker list to produce a dictionary that is used to group
    statistics returned from the calculation module into the categories that are 
    required in our output.

    Marker list file will be in format as described below:

    # LOCUS NAME\tLOCUS POSITION\tGENOTYPE\tCATEGORY\tLABEL\tPROCEDURE
    pfdhps\t436\tC\tpfdhps 436c\tPure
    
    The CATEGORY AND LABEL fields are optional and will only be used if present
    when producing output files. Dictionary structure housing the values parsed
    from the input file below:
    
    dict = (LOCUS NAME, LOCUS POSITION, GENOTYPE) = { 
                category: CATEGORY
                label: LABEL

    If the PROCEDURE field is defined we will want to store all of the information
    for this line in our marker list into our marker combination list:
        [ 'locus name1', 'locus position1', 'genotype1 .... ]
    """
    markerLookup = {}
    combinationsList = []        

    markerListFH = open(markerList)
    for line in markerListFH:
        if line.startswith('#'):
            continue

        # TODO: Work in code that handles combination markers
        (nameRaw, posRaw, type, genotypeRaw, category, label, procedure) = line.rstrip('\n').split('\t')

        name = commaDelimToTuple(nameRaw)
        pos = commaDelimToTuple(posRaw)
        genotype = commaDelimToTuple(genotypeRaw)            

        # Our marker tuple is created by zip'ing our name and pos variables
        markerTuple = tuple(zip(name, pos))

        # Set defaults for our dictionary
        markerLookup.setdefault(markerTuple, {} )
        markerLookup.get(markerTuple).setdefault('valid', [])
        markerLookup.get(markerTuple).setdefault(genotype, {})

        # All valid genotypes for a given marker (locus name + position) 
        # are placed into a list that will be used when printing output
        markerLookup.get(markerTuple).get('valid').append(genotype)        

        # On a per-genotyped basis we want to store the category that this genotype
        # will be grouped under as well as the label (i.e. Pure, Mixed).        
        markerLookup[markerTuple][genotype]['category'] = category
        markerLookup[markerTuple][genotype]['label'] = label

        if procedure:
            combinationsList.append([procedure, zip(name, pos, genotype)])

    markerListFH.close()
    return (markerLookup, combinationsList)

def commaDelimToTuple(str):
    """
    Splits a comma-delimited list and converts it to a tuple
    """
    return tuple(str.split(','))

def createMysqlIterator(config, queryParams, cnBins, comboList):
    """
    Takes a configuration file containing login credentials to the WWARN DB and 
    a set of query parameters to contruct a query to pull down data that will be 
    used in generating our calculations. Yields a list of data for each line of results.

    TODO: Work in combination marker queries 
    """
    # We return a list of our query parameters here because we need our where statement
    # when firing off our stored procedures for our combination markers
    queryList = buildQueryStatement(queryParams)
    query = " ".join(queryList)

    dbConn = openDBConnection(config)
    dbCursor = dbConn.cursor()
    dbCursor.execute(query)
    rows = dbCursor.fetchall()

    ## Now execute all our stored procedure calls
    comboRows = getCombinationMarkerData(dbConn, queryList[2], comboList)
    dbCursor.close()
    
    # Merge our two sets of results
    # We probably want to find a better way to do this rather than storing everything in memory
    rows = rows[1:] + comboRows

    # Process the rows 
    for row in rows:
        marker = row[6]
        genotype = row[7]

        # Have to convert 'Copy Number' to 'CN' and 'Genotype Fragment' to 'FRAG'
        marker.replace('Copy Number', 'CN')
        marker.replace('Genotype Fragment', 'FRAG')

        # Check to see if our marker type is copy number (and in the future 
        # genotype fragment)
        if marker.find('CN') != -1 and genotype not in ['Genotyping failure', 'Not genotyped']:
             genotype = preBinCopyNumberData(genotype, cnBins)

        yield row

def buildQueryStatement(params):
    """
    Builds the query statement sent off to the database.

    This is a placeholder function that will involve much more once this script
    is convereted to CGI
    """
    selectStmt = "SELECT s.label, s.investigator, l.country, l.site, p.patient_id, p.age, " \
                 "CONCAT(m.locus_name, \"_\", m.locus_position, \"_\", m.type) AS \"marker\", g.value "
    fromStmt = "FROM study s JOIN location l ON s.id_study = l.fk_study_id " \
               "JOIN subject p ON p.fk_location_id = l.id_location AND p.age IS NOT NULL " \
               "JOIN sample sp ON sp.fk_subject_id = p.id_subject " \
               "JOIN genotype g ON g.fk_sample_id = sp.id_sample " \
               "JOIN marker m ON m.id_marker = g.fk_marker_id "
    
    # If params was passed in we want to concat it to our query 
    whereStmt = ""
    if params:
        whereStmt = "WHERE %s" % params            
    
    return [selectStmt, fromStmt, whereStmt]

def openDBConnection(config):
    """
    Opens a database connection to the specified database using the provided
    credentials.

    Returns an open MySQLdb connection object 
    """
    hostname = config.get('DB', 'hostname')
    dbName = config.get('DB', 'database_name')
    username = config.get('DB', 'username')
    password = config.get('DB', 'password')

    dbConn = MySQLdb.connect(host=hostname, user=username, passwd=password, db=dbName)
    return dbConn

def getCombinationMarkerData(conn, params, combinations):
    """
    Takes a list of combinations and the stored procedure name
    in our WWARN db that will generate results and executes each
    adding any parameters (WHERE clause params) to each procedure call.

    Results are appended to the list already containing data from 
    our query to pull down all single marker data
    """ 
    results = ()

    # Because our parameters will be appened onto an already built SQL
    # statement we are going to want to replace our WHERE with an AND.        
    params = params.replace('WHERE', 'AND')

    for combo in combinations:
        # Need to open a new cursor for each query, shortcoming of mysqldb
        cursor = conn.cursor()

        procedure = combo[0]
        argsList = list(chain(*combo[1]))
        argsList.append(params)

        procedureStmt = "call %s(%s)" % (procedure, ",".join(["%s"] * len(argsList)))

        cursor.execute(procedureStmt, (argsList))
        rows = cursor.fetchall()
        
        results = results[1:] + rows

        # Close the cursor to make sure we don't run into any errors on our next query
        cursor.close()

    return results       

def write_statistics_to_file(stats, outFile, groups):
    """
    Writes out a subset of our calculation data using the 
    groups list passed in
    """
    calcsFH = open(outFile, 'w')

    # Write our header to file
    header = ['STUDY_ID', 'STUDY_LABEL', 'COUNTRY', 'SITE', 'INVESTIGATOR',
               'GROUP', 'MARKER', 'GENOTYPE', 'SAMPLE SIZE', 'PREVALENCE',
               'PREVALENCE RAW', 'GENOTYPED']
    calcsFH.write("\t".join(header))
    calcsFH.write("\n")
   
    # Now iterate over our statistics dictionary and print out the data we 
    # need    
    for (metadata, locusIter) in stats.iteritems():
        for (marker, genotypesIter) in locusIter.iteritems():
            # Need to pop this key/value off our dictionary so we 
            # can loop over only actual genotypes
            sampleSizeDict = genotypesIter.pop('sample_size')
            
            for genotype in genotypesIter:
                for group in groups:
                    sampleSize = str(sampleSizeDict.get(group))
                    prevalenceRaw = genotypesIter[genotype][group]['prevalence']
                    prevalence = "{0:.0%}".format(prevalenceRaw)
                    genotyped = str(genotypesIter[genotype][group]['genotyped'])

                    rowList = []
                    rowList.append("")
                    rowList.extend(list(metadata))
                    rowList.append(group)
                    rowList.append(marker)
                    rowList.append(genotype)
                    rowList.extend([sampleSize, prevalence, str(prevalenceRaw), genotyped])

                    calcsFH.write("\t".join(rowList))
                    calcsFH.write("\n")

    calcsFH.close()

def generateGroupedStatistics(data, markerMap, groups):
    """
    Group our statistics by cateory and label provided in the marker
    mapping file.
    """
    groupedStats = {}
    
    # Need to add the 'ALL' key to our groups (which right now consi
    groups.append('All')

    for (metadataKey, locusIter) in data.iteritems():
        for (markerKey, genotypesIter) in locusIter.iteritems():
            # Snatch the sample size out for this marker
            sampleSizeDict = genotypesIter.get('sample_size')

            if not markerKey in markerMap:
                print "DEBUG: Marker %r not in map" % markerKey
                continue

            # Now grab the list of all valid genotypes to iterate over
            # and check to see if the genotype exists in our statistics
            validGenotypes = markerMap.get(markerKey).get('valid')

            for genotype in validGenotypes:
                genotypeStats = data[metadataKey][markerKey].get(genotype, None)
                markerCategory = markerMap[markerKey][genotype].get('category')
                genotypeLabel = markerMap[markerKey][genotype].get('label')

                for group in groups:
                    # Initialize our dictionary if it hasn't already been.
                    (groupedStats.setdefault(metadataKey, {})
                                 .setdefault(markerCategory, {})
                                 .setdefault(genotypeLabel, {})
                                 .setdefault(group, {})
                                 .setdefault('genotyped', 0))
                    (groupedStats.setdefault(metadataKey, {})
                                 .setdefault(markerCategory, {})
                                 .setdefault(genotypeLabel, {})
                                 .setdefault(group, {})
                                 .setdefault('prevalence', 0))

                    # Initialize our sample size (if it already hasn't been)
                    (groupedStats[metadataKey][markerCategory]
                                 .setdefault('sample_size', sampleSizeDict))
                                 
                    # Grab the genotyped and prevalence for this genotype and 
                    # add to the value currently there. If statistics do not exist
                    # for this genotype do nothing.
                    if genotypeStats:
                        groupStats = genotypeStats.get(group, None)
                        genotypedCount = groupStats.get('genotyped', 0)
                        prevalence = groupStats.get('prevalence', 0)

                        groupedStats[metadataKey][markerCategory][genotypeLabel][group]['genotyped'] += genotypedCount
                        groupedStats[metadataKey][markerCategory][genotypeLabel][group]['prevalence'] += prevalence

    return groupedStats                        

def main(parser):
    wwarnCalcDict = {}

    # Parse our age and copy number groups to allow us to further group 
    # our results
    ageGroups = parseAgeGroups(parser.age_groups)
    copyNumberGroups = parseCopyNumberGroups(parser.copy_number_groups)

    # Parse our config file
    config = ConfigParser.RawConfigParser()
    config.read(parser.config_file)

    # Parse our marker list to provide us with two pieces of data needed
    # in our  calculations process:
    #
    #       1.) Groupings of markers (i.e. dhps436C Pure)
    #       2.) Our combination marker genotypes (i.e. dhps double = dhps437G + dhps540E)
    (markerGroups, markerCombos) = parseMarkerList(parser.marker_list)

    # Now we can move onto generating our calculations
    dataIter = createMysqlIterator(config, parser.query_params, copyNumberGroups, markerCombos)
    calculateWWARNStatistics(wwarnCalcDict, dataIter, ageGroups)

    # Before we can print our output we need to group all our statistics together under the 
    # categories and labels found in our marker map
    ageLabels = [t[2] for t in ageGroups]
    groupedStats = generateGroupedStatistics(wwarnCalcDict, markerGroups, ageLabels)

    # Our statistics need to be written to two files:
    #       1.) Statistics not grouped by age
    #       2.) Statistics grouped by age
    allFile = join(parser.output_directory, parser.output_prefix + '.all.calcs')
    ageFile = join(parser.output_directory, parser.output_prefix + 'ags.calcs')

    write_statistics_to_file(groupedStats, allFile, ['All'])
    write_statistics_to_file(groupedStats, ageFile, ageLabels)

if __name__ == "__main__":
    main(buildArgParser())

