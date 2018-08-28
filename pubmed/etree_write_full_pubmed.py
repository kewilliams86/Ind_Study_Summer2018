# -*- coding: utf-8 -*-
"""
Created on Sat Aug 25 17:07:13 2018

@author: kewil
"""

# -*- coding: utf-8 -*-
"""
@author kewilliams

Usage:

  write_full_pubmed_to_text.py [-h] username password inputDirectory outputDirectory

Extract dcast article information from PubMed xml files

positional arguments:
  username         dcast username
  password         dcast password
  inputDirectory   directory of input files
  outputDirectory  directory of output files

Tests against dcast database for matching pmids in the PubGene table

"""

import shutil #move file location
import timeit
import mysql.connector
from mysql.connector import errorcode
import xml.etree.ElementTree as ET
import gzip

import sys
import argparse
import glob
import os

def unzipFile(file):
    f = gzip.open(file, 'rb')
    pubTree = ET.parse(f)
    f.close()
    return pubTree


#taken from medline_parser.py
def getPmid(medline):
    
    if medline.find('PMID') is not None:
        pmid = medline.find('PMID').text
    else:
        pmid = ''
    return pmid


def getTitle(article):
    
    if article.find('ArticleTitle') is not None:
        title = article.find('ArticleTitle').text
    else:
        title = ''
    return title


def getAuthor(article):
    
    authorString = ''
    #no authors needs to be tested from the article branch
    if article.find('AuthorList') is not None:
        authors = article.findall('AuthorList/Author')
        for author in authors:
            if author.find('Initials') is not None:
                authorString += author.find('Initials').text + ' '
            else:
                authorString += ''
            if author.find('LastName') is not None:
                authorString += author.find('LastName').text + '; '
            else:
                authorString += '; '
        return authorString[:-2] #remove '; ' after last author
    else:
        return authorString
            

def getJournal(journal):

    if journal.find('Title') is not None:
        journalTitle = journal.find('Title').text
    else:
        journalTitle = ''
    return journalTitle
        

def getPubDate(pubDate):
    
    if pubDate.find('Year') is not None:
        year = pubDate.find('Year').text
    #if no child Year, child MedlineDate may replace it. Formatted 'Year Month'
    elif pubDate.find('MedlineDate') is not None:
        year = pubDate.find('MedlineDate').text.split(' ')[0]
    else:
        year = ''
    return year


def getAbstract(article):
    
    if article.find('Abstract/AbstractText') is not None:
        abstracts = article.findall('Abstract/AbstractText')
        if len(abstracts) == 1:
            abstractText = abstracts[0].text
        elif len(abstracts) > 1:
            abstractText = ''
            for abstract in abstracts:
                if (abstract.attrib.get('NlmCategory', 'null')) != 'null':
                    abstractText += abstract.attrib.get('NlmCategory', '') + ' ' + abstract.text + ' '
                elif (abstract.attrib.get('Label', 'null')) != 'null':
                    abstractText += abstract.attrib.get('Label', '') + ' ' + abstract.text + ' '
                else:
                    abstractText += abstract.text + ' '
            abstractText = abstractText[:-1]
        else:
            abstractText = ''
    elif article.find('Abstract') is not None:
        abstractText = article.find('Abstract').text
    else:
        abstractText = ''
    return abstractText


#database access for pmids
def dCastDatabase (userName, password, inputDirectory, outputDirectory):
    try:
        cnx = mysql.connector.connect(user=userName, password=password,
                                      database='dcast')
    except mysql.connector.Error as err:
        
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        createTxtFromXML(inputDirectory, cnx)
        cnx.close()

def createTxtFromXML(filePath, cnx):

    t2 = timeit.default_timer()
    
    query = ("select PMID from PubGene where PMID = ") #generic query
    errorStr = "" #for try / catch
    
    # get all xml.gz files in specified directory
    files = sorted(glob.glob(filePath +"/*.xml.gz"))
    print("Number of *.xml.gz files found in directory '", filePath, "': ", len(files), sep = "")

    # create outputDirectory if it does not exist
    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)

    errorCount = 0

    for inFile in files:
        t0 = timeit.default_timer()
        
        try:
            pubTree = unzipFile(inFile)
        
        except :            
            if not os.path.exists(outputDirectory + ("/ERRORS/")): #create folder for failed file
                os.makedirs(outputDirectory + ("/ERRORS/"))
            shutil.copy(inFile, outputDirectory + "/ERRORS/" + os.path.basename(inFile)) #move to ERROR folder
            errorStr = os.path.basename(inFile) + " - " + str(sys.exc_info()[0])
            print(errorStr)
            f = open(outputDirectory + "/ERRORS/log.txt", "a")
            f.write(errorStr + "\n")
            f.close()
            errorCount += 1
            continue #skip to next file
        
             
        outFile = outputDirectory + "/extracted_" + os.path.basename(inFile).replace(".xml.gz", ".txt")
        
        writeFile = open(outFile, 'w') #open file for data transfer
        
        #unbuffered fetchone() causes error after a large amount of queries, reusing a cursor
        #repeatedly without fetching all results leads to "unread result found"
        #buffered allows all results to be fetched, but only returns one to code
        cursor = cnx.cursor(buffered=True)
        
        for pubmedArticle in pubTree.getiterator('PubmedArticle'):
            cursor.execute(query + getPmid(pubmedArticle.find('MedlineCitation')))
            row = cursor.fetchone()
            if row != None:
                writeToFile(pubmedArticle, writeFile)
        cursor.close()
        t1 = timeit.default_timer()
        print("Successful Write : " + outFile + " : " + str(t1 - t0))   
    
    #unnecessary unless try / catch 
    t3 = timeit.default_timer()
    print("\nTotal time of execution: " + str(t3 - t2))
    if errorCount is not 0 :
        print("\nWarning:", errorCount, "files could not written. See", outputDirectory + "/ERRORS/log.txt for more information")
        


def writeToFile (pubmedArticle, writeFile):
    
    writeFile.write(ascii(getPmid(pubmedArticle.find('MedlineCitation'))) + '\t' +
                    ascii(getTitle(pubmedArticle.find('MedlineCitation/Article'))) + '\t' +
                    ascii(getAuthor(pubmedArticle.find('MedlineCitation/Article'))) + '\t' +
                    ascii(getJournal(pubmedArticle.find('MedlineCitation/Article/Journal'))) + '\t' +
                    ascii(getPubDate(pubmedArticle.find('MedlineCitation/Article/Journal/JournalIssue/PubDate'))) + '\t' +
                    ascii(getAbstract(pubmedArticle.find('MedlineCitation/Article'))) + '\n') 
    

# main program
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser(description='Extract dcast article information from PubMed xml files')
ap.add_argument("username", help="dcast username")
ap.add_argument("password", help="dcast password")
ap.add_argument("inputDirectory", help = "directory of input files")
ap.add_argument("outputDirectory", help = "directory of output files")

# print help if no arguments are provided
if len(sys.argv)==1:
    ap.print_help(sys.stderr)
    sys.exit(1)

args = vars(ap.parse_args())

userName = args['username']
password = args['password']

inputDirectory = args['inputDirectory']
outputDirectory = args['outputDirectory']

#path for xml and text files, only necessary change for user
dCastDatabase(userName, password, inputDirectory, outputDirectory)