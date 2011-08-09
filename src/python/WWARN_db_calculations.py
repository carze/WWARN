#!/usr/bin/env python

##
# This script (soon to be CGI script) queries the back-end WWARN database to perform a 
# calculation on either a specific dataset pulled from the database (query with criteria)
# or the full set of data from the database.
#

import MySQLdb
import argparse
import ConfigParser
import datetime

from collections import OrderedDict
from os.path import join
from itertools import chain
from wwarncalculations import calculateWWARNStatistics
from wwarnutils import parseAgeGroups, parseCopyNumberGroups, preBinCopyNumberData

from wwarnutils import pprint

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
    parser.add_argument('-s', "--study_ids", required=False, action='append', default=[], help="A specific study ID " 
                        + "on which to query data upon and perform calculations on.")
    parser.add_argument('-si', "--sites", required=False, action='append', default=[], help="A specific site on which " 
                        + "to query data upon and perform calculations on.")
    parser.add_argument("-b", "--bin-by-year", required=False, help="Bin all studies by a year range. " 
                        + "This year range should be defined in a digit representing the number of years " 
                        + "to create bins with (i.e. 1 = 1 year = 365 days)", type=int, dest="year_step")
    parser.add_argument("-d", "--debug", required=False, help="Turn on debug printing", action='store_const', const=True,
                        default=False)
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
    combinationsList = {}

    markerListFH = open(markerList)
    for line in markerListFH:
        if line.startswith('#'):
            continue

        (nameRaw, posRaw, type, genotypeRaw, category, label, procedure) = line.rstrip('\n').split('\t')

        name = commaDelimToTuple(nameRaw)
        pos = commaDelimToTuple(posRaw)
        genotype = commaDelimToTuple(genotypeRaw)            

        markerTuple = tuple(zip(name, pos))

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

        # In order to adequately deal with combination markers we 
        # need to create a separate data structure to contain 
        # the stored procedure call we will use as well as the
        # arguments that should be passed to the procedure.
        if procedure and procedure not in combinationsList:
            combinationsList[procedure] = zip(name, pos)

    markerListFH.close()
    return (markerLookup, combinationsList)

def commaDelimToTuple(str):
    """
    Splits a comma-delimited list and converts it to a tuple
    """
    return tuple(str.split(','))

def createMysqlIterator(config, studyIds, sites, cnBins, comboList, year_step):
    """
    Takes a configuration file containing login credentials to the WWARN DB and 
    a set of query parameters to contruct a query to pull down data that will be 
    used in generating our calculations. Yields a list of data for each line of results.
    """
    queryList = buildQueryStatement(studyIds, sites)
    query = " ".join(queryList)

    dbConn = openDBConnection(config)
    dbCursor = dbConn.cursor()
    params = studyIds + sites

    dbCursor.execute(query, params)
    rows = dbCursor.fetchall()
    dbCursor.close()

    comboRows = getCombinationMarkerData(dbConn, queryList[2], params, comboList)
    
    ## If we are also splitting by year-bins we need to generate our year ranges
    year_bins = None
    if year_step:
        # Will need the lower bound and upper bound of the dates in order to 
        # generate our date bins
        year_bounds = get_date_bounds(dbConn, queryList, params)
        year_bins = create_year_bins(year_step, year_bounds)
        print year_bins


    rows = rows[0:] + comboRows
    for row in list(rows):
        print row
        label = row[1]
        doi = row[7]
        site = row[4]
        marker = row[8]
        genotype = row[9]

        # Update our site if we are binning by years
        site = parse_site(site, label, doi, year_bins)
        row = row[0:4] + (site,) + row[5:7] + row[8:]

        # Convert to abbreviated format to match listing in valid marker file
        marker = marker.replace('Copy Number', 'CN')
        marker = marker.replace('Genotype Fragment', 'FRAG')
        
    
        # Check to see if our marker type is copy number (and in the future 
        # genotype fragment)
        if marker.find('CN') != -1 and genotype not in ['Genotyping Failure', 'Not Genotyped']:
            genotype = preBinCopyNumberData(genotype, cnBins)
            row = row[0:8] + (marker, genotype)

        yield row
    
def parse_site(site, label, doi, year_bins):
    """
    Attempts to bin a site using the generate year ranges if they were 
    generated otherwise returns the site untouched.
    """
    if year_bins:
        site_bins = year_bins[label][site]
        for (lower, upper) in site_bins:
            if lower <= doi < upper:
                site = "%s_%s-%s" % (site, lower.year, upper.year)
    
    return site 

def buildQueryStatement(studyIds, sites):
    """
    Builds the query statement sent off to the database.

    This is a placeholder function that will involve much more once this script
    is convereted to CGI
    """
    selectStmt = "SELECT s.wwarn_study_id, s.label, s.investigator, l.country, l.site, p.patient_id, p.age, " \
                 "p.date_of_inclusion, CONCAT(m.locus_name, \"_\", m.locus_position, \"_\", m.type) AS \"marker\", g.value "
    fromStmt = "FROM study s JOIN location l ON s.id_study = l.fk_study_id " \
               "JOIN subject p ON p.fk_location_id = l.id_location " \
               "JOIN sample sp ON sp.fk_subject_id = p.id_subject " \
               "JOIN genotype g ON g.fk_sample_id = sp.id_sample " \
               "JOIN marker m ON m.id_marker = g.fk_marker_id "
    
    whereStmt = "WHERE "
    if studyIds:
        whereStmt += buildWhereStmt('s.wwarn_study_id', studyIds)

    if sites:        
        whereStmt += buildWhereStmt('l.site', sites)
    
    whereStmt = whereStmt.rstrip(" AND ")
    whereStmt = whereStmt.rstrip("WHERE ")
    return [selectStmt, fromStmt, whereStmt]

def buildWhereStmt(key, values):
    """
    Constructs the where statement portion of our query based off the key and 
    values passed in. For each value a key = %s placeholder is generated 
    to be replaced during the query execute.
    """
    where = " ("

    for val in values:
        where += key + "=%s OR "
    
    where = where.rstrip("OR ")
    where += ") AND "
    return where

def create_year_bins(step, bounds):
    """
    Creates a list of tuples containing the pots to bin all our studies 
    when creating calculations. Each tuple will contain datetime objects
    containing the bounds of the bin, i.e. ('2007-02-01', '2009-02-01')
    """
    year_bins = {}

    for (label, site, lower, upper) in bounds:
        year_bins.setdefault(label, {})[site] = (date_range(lower, upper, datetime.timedelta(365 * step)))
        
    return year_bins 
                
def date_range(start, stop, step):
    """
    Generates a range of dates in the format (A, B), (B, C), (C, D) etc.
    """
    output = []

    if start < stop:
        cmp = lambda a, b: a < b
        inc = lambda a: a + step
    else:
        cmp = lambda a, b: a > b
        inc = lambda a: a - step

    while cmp(start, stop):
        end = inc(start)
        output.append( (start, end) )  
        start = end
    
    return output        

def get_date_bounds(conn, query_components, params):
    """
    Gets the lower and upper bound of dates for the given study.
    """
    cursor = conn.cursor()

    query = "SELECT s.label, l.site, MIN(p.date_of_inclusion), MAX(p.date_of_inclusion) " + query_components[1] + query_components[2]
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()           
    
    for row in rows:
        yield row
    
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

def getCombinationMarkerData(conn, where_stmt, params, combinations):
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
    where_stmt = where_stmt.replace('WHERE', 'AND')
    where_stmt = where_stmt % tuple(['"%s"' % x for x in params])

    for procedure in combinations:
        # Need to open a new cursor for each query, shortcoming of mysqldb
        cursor = conn.cursor()

        argsList = list(chain(*combinations[procedure]))
        argsList.append(where_stmt)

        procedureStmt = "call %s(%s)" % (procedure, ",".join(["%s"] * len(argsList)))

        cursor.execute(procedureStmt, (argsList))
        rows = cursor.fetchall()
        results = results[0:] + rows
        cursor.close()

    return results       

def write_statistics_to_file(stats, outFile, groups, debug):
    """
    Writes out a subset of our calculation data using the 
    groups list passed in
    """
    calcsFH = open(outFile, 'w')

    # Write our header to file
    header = ['STUDY_ID', 'STUDY_LABEL', 'COUNTRY', 'SITE', 'INVESTIGATOR',
               'GROUP', 'MARKER', 'GENOTYPE', 'SAMPLE SIZE', 'PREVALENCE']

    if debug:
        header.extend(['PREVALENCE RAW', 'GENOTYPED'])
                       
    calcsFH.write("\t".join(header))
    calcsFH.write("\n")
   
    # Now iterate over our statistics dictionary and print out the data we 
    # need    
    for (metadata, locusIter) in stats.iteritems():
        for (marker, genotypesIter) in locusIter.iteritems():
            # Need to pop this key/value off our dictionary so we 
            # can loop over only actual genotypes
            sampleSizeDict = genotypesIter.get('sample_size')
            
            for genotype in genotypesIter:
                # Can't pop 'sample_size' off our genotypesIter dictionary
                # as we call this function twice
                if genotype == "sample_size": continue

                for group in groups:
                    sampleSize = str(sampleSizeDict.get(group))
                    prevalenceRaw = genotypesIter[genotype][group]['prevalence']
                    prevalence = "{0:.0%}".format(prevalenceRaw)
                    genotyped = str(genotypesIter[genotype][group]['genotyped'])

                    rowList = []
                    rowList.extend(list(metadata))
                    rowList.append(group)
                    rowList.append(marker)
                    rowList.append(genotype)
                    rowList.append(sampleSize)
                    rowList.append(prevalence)

                    if debug:
                        rowList.extend([str(prevalenceRaw), genotyped])

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

    config = ConfigParser.RawConfigParser()
    config.read(parser.config_file)
    ageGroups = parseAgeGroups(config.get('GENERAL', 'age_groups'))
    copyNumberGroups = parseCopyNumberGroups(config.get('GENERAL', 'copy_number_groups'))
    (markerGroups, markerCombos) = parseMarkerList(parser.marker_list)

    dataIter = createMysqlIterator(config, parser.study_ids, parser.sites, copyNumberGroups, markerCombos, parser.year_step)
    calculateWWARNStatistics(wwarnCalcDict, dataIter, ageGroups)

    # Before we can print our output we need to group all our statistics together under the 
    # categories and labels found in our marker map
    ageLabels = [t[2] for t in ageGroups]
    groupedStats = generateGroupedStatistics(wwarnCalcDict, markerGroups, ageLabels)

    # Our statistics need to be written to two files:
    #       1.) Statistics not grouped by age
    #       2.) Statistics grouped by age
    allFile = join(parser.output_directory, parser.output_prefix + '.all.calcs')
    ageFile = join(parser.output_directory, parser.output_prefix + '.age.calcs')

    write_statistics_to_file(groupedStats, allFile, ['All'], parser.debug)
    write_statistics_to_file(groupedStats, ageFile, ageLabels, parser.debug)

if __name__ == "__main__":
    main(buildArgParser())
