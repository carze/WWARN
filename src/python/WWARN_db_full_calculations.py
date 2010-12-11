###
# This script executes the WWARN calculations utilizing a full database query 
# (no criteria used to filter results) to provide the data needed.


import sys
import os
import argparse
import MySQLdb

def buildArgParser():
    """
    Creates an argparser object using the command-line arguments passed into this script
    """
    parser = argparse.ArgumentParser(description='Produces sample size and prevalence calculations '
                                        + 'given data provided from the WWARN database')
    parser.add_argument('-m', '--marker_list', help='A list of all possible markers that should be '
                            + 'looked at in tabulating these statistics.')
    parser.add_argument('-d', '--database_name', help='Name of database to query data from. Should '
                            + 'be a database using the WWARN schema')
    parser.add_argument('-h', '--database_host', help='Hostname of server housing databaset to query')                                                        
    parser.add_argument('-u', '--username', help='Database login username')
    parser.add_argument('-p', '--password', help='Database login password')
    parser.add_argument('-o', '--output_file', help'Desired output file containing WWARN calculations')
    args = parser.parse_args()

    return args

def openDBConnection(hostname, dbName, username, password):
    """
    Opens up a connection to the databased specified by the passed-in function arguments

    Returns an open MySQLdb connection object to our specified database
    """
    connection = MySQLdb.connect(host=hostname, db=dbName, user=username, passwrd=password)
    return connection

def parserMarkerList(inputList):
    """
    Parses the provided marker list and creates a dictionary housing our single markers and combination 
    markers
    """
    markerFh = open(inputList)

    for line in markerFh:
        tokens = line.split('\t')

        ## Our marker list file should be in the format 

def generateWWARNResultsFromDB(conn, markerList):
    """
    Builds and executes the query required to generate data needed for sample size and prevalence
    calculations. 
    """
    ## We want to start off by parsing our marker list 

def main(parser):
    dbConn = None

    ## Start off by opening up a connection to our database
    dbConn = openDBConnection(parser.database_host, parser.database_name, parser.username, parser.password)

    markerList = parseMarkerList(parser.marker_list)

    ## Once we have our connection open we can go about executing the query we need to get data
    dbResults = generateWWARNResultsFromDB(dbConn, parser.marker_list)

    
    pass
    
if __main__ == "__main__":
    main(buildArgParser())
