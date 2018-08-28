# -*- coding: utf-8 -*-
"""
Created on Thu May 24 14:46:32 2018

@author: kewilliams

I did the thesaurus comparisons two ways. If there is high confidence in the
accuracy of the text file codes, the first method is better "findSyn".  If there
is a likelihood of invalid codes the second method works better because a bad code
won't mess up all following codes "findSynAlt".  Any duplicate of codes
is removed, but a completely invalid code will return null for itself and every 
following code in the first method.  The first method is a single iteration 
through the thesaurus vs an iteration for each code
"""

import argparse
import sys

from nltk.stem import SnowballStemmer
from words import stemWords 

#create multidimensional list from codefile
def createTable(codeFile):
    
    #list of codes
    lines = [line.strip() for line in open(codeFile)]
    synList = [l for l in lines if l != ""]
    synList = list(set(synList)) #remove duplicates
    
    #create multidimensional list for synonym values
    synTable = [["null" for column in range(4)] for row in range(len(synList))]
    for i in range(len(synList)):
        synTable[i][0] = synList[i]
        
    return synTable


#convert str line in thesaurus to list, compare and retrieve data from 
#relevant entries, add entries to table
def findSyn(thesFile, synTable):
    
    #the thesaurus is sorted, in order to do a single iteration through it,
    #synonym codes must also be sorted
    synTable.sort()

    index = 0
    with open(thesFile) as readFile: #open thesaurus
        for line in readFile:
            data = line.split('\t') #thesaurus is tab delimited, split to list
            if data[0] == synTable[index][0]: #data[0] contains code identifiers
                synTable[index][1] = data[3] #data[3] contains the synonym list
                modStr = modifiedSyn(data[3]) #run function to modify synonyms
                synTable[index][2] = modStr
                synTable[index][3] = data[3].split("|")[0] # first synonym is preferred name
                index += 1
                if index >= len(synTable): #stop search once all codes are found
                    break
                
    return synTable

def findSynAlt(thesFile, synTable):
    
    #method to allow for invalid codes to be returned as null without
    #causing all following codes to be returned as null

    for i in range(len(synTable)):
        with open(thesFile) as readFile: #open thesaurus
            for line in readFile:
                data = line.split('\t') #thesaurus is tab delimited, split to list
                if data[0] == synTable[i][0]: #data[0] contains code identifiers
                    synTable[i][1] = data[3] #data[3] contains the synonym list
                    modStr = modifiedSyn(data[3]) #run function to modify synonyms
                    synTable[i][2] = modStr
                    break
        if (synTable[i][1] == "null"):
            print(synTable[i][0] + " is an invalid code")
    
    return synTable
    
    
#takes string of synonyms from the thesaurus and removes redundancy 
def modifiedSyn(initSyn):    
        
    data = initSyn.lower().split('|') #turn to lowercase list

    # getStems - also takes care of punctuation and words which are too short
    data = [stemWords(x) for x in data]
    data = [d for d in data if d is not '']

    #order from smallest to largest string to allow single pass through list
    data.sort(key=lambda x: len(x))
   


    temp = []
    synStr = ""
    for item in data:
        if not any(syn in item for syn in temp): #redundancy test
            temp.append(item) #update temp list with valid items
            synStr += item + '|' #concatenate valid synonyms + '|'
    
    return synStr[:-1] #return string without final character ('|')

#write to desired tab delimited file
#syn code \t original thesaurus arguments \t modified thesaurus \n
def printSyn(outFile, synTable):

#    from nltk.stem import SnowballStemmer
#    snow = SnowballStemmer('english')

    writeFile = open(outFile, 'w')
    writeFile.write("Code\tTerm\tSynonyms\tPattern\n")
    for i in range(len(synTable)):
        writeFile.write(synTable[i][0] + '\t' + synTable[i][3] +'\t' + synTable[i][1] + '\t' + 
                        synTable[i][2] + '\n')
#        print(synTable[i][0] + '\t' + synTable[i][1] + '\t' + 
#              synTable[i][2] + '\n')

def main():  

  # main program
  # construct the argument parse and parse the arguments
  ap = argparse.ArgumentParser(description='Look up codes in NCIthesaurus')
  ap.add_argument("thesaurus", help = "text file containing the thesaurus (FLAT format), from https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/")
  ap.add_argument("codes", help = "file containing codes, 1 per line")
  ap.add_argument("outputFile", help = "name of output file")

  # print help if no arguments are provided
  if len(sys.argv)==1:
    ap.print_help(sys.stderr)
    sys.exit(1)

  args = vars(ap.parse_args())

  thesFile = args['thesaurus']
  codeFile = args['codes']
  outFile = args['outputFile']

    #file names
    
    #codeFile = "codes.txt"
    #outFile = "synonyms.txt"
    
  synTable = createTable(codeFile)
    
  synTable = findSyn(thesFile, synTable)
  printSyn(outFile, synTable)
    
if __name__  == "__main__":
    main()
