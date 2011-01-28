#!/usr/bin/env python

##
# This script (soon to be CGI script) queries the back-end WWARN database to perform a 
# calculation on either a specific dataset pulled from the database (query with criteria)
# or the full set of data from the database.
#

import MySQLdb
import argparse
import ConfigParser
import profile

from collections import OrderedDict
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

        markerLookup.setdefault( (name, pos, type, genotype), {} )
        markerLookup[(name, pos, type, genotype)]['category'] = category
        markerLookup[(name, pos, type, genotype)]['label'] = label

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

def generateGroupedStatistics(stats, map):
    """
    Groups together sets of statistics based off of labels found in our 
    marker lookup i.e.:
        pfdhps 436 C = pfdhps 436C - Pure
        pfdhps 436 A/C = pfdhps 436C Mixed
        pfdhps 436 S/C = pfdhps 436C Mixed 

    We would group together prevalence and sample size calculations for the two 'Mixed' genotypes
    like so pfdhps 436C Mixed = pfdhps 436 A/C sample Size + pfdhps 436 S/C sample size        
    """
    pass
#    groupedStats = {}
#
#    for (metadataKey, locusIter) in stats.iteritems():
#        for (markerKey, genotypesIter) in locusIter.iteritems():
#            for genotype in genotypesIter:
                ## Couple things we want to do here:
                # 
                #     1.) Check the locus name + locus pos + genotype against
                #         our marker lookup table to see what category this 
                #         may fall under (e.x. pfdhps436C)
                #
                #     2.) See if this marker has a label (i.e. 'Pure' or 'Mixed')
                #     3.) Based off #1 and #2 we may have to
#                locusName = markerKey[0]
#                locusPos = markerKey[1]
                
#                category = map[(locusName, locusPos, genotype)].get('category', None)
#                markerLabel = map[(locusName, locusPos, genotyoe]].get('label', None)

                # We want to skip this data if it doesn't contain a category
#                if category is not None:
#                    groupedStats.setdefault(category, {}).setdefault(

def writeStatisticsToFile(stats, outDir):
    """
    Writes out four files each containing statistics separated by category:

        1.) Sample size
        2.) Sample size grouped by age
        3.) Prevalence 
        4.) Prevalence grouped by age
    """
    pass

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

    # Finally print our output to files
    #writeStatisticsToFile(generateGroupedStatistics(wwarnCalcDict, markerMap), parser.output_directory)

if __name__ == "__main__":
    profile.run( 'main(buildArgParser())' )


