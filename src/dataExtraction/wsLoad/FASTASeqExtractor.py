#!/usr/bin/env python

import io
import re
import sys
import json

import Bio.Seq
import Bio.SeqRecord
import Bio.Alphabet

class FASTASeqExtractor(object):

    def __init__(self, filePath):
        self._sourceFile = filePath
        self._sequences = dict()


    def _extractHeaders(self):
        inFile = io.open(self._sourceFile, 'r')

        # get the file length and track the end of file
        inFile.seek(0,2)
        eof = inFile.tell()
        inFile.seek(0)

        # read at most 1GB at once
        chunkSize = 2**30

        # if the file is smaller than the chunkSize just read the whole file
        if chunkSize > eof:
            chunkSize = eof

        start = 0
        stop = 0
        while start < eof:
            chunk = inFile.read(chunkSize)
            stop = inFile.tell()

            lastFound = 0
            while start + lastFound < eof:
                headerStart = chunk.find(">", lastFound)

                if headerStart == -1:
                    inFile.close()
                    raise Exception("Unable to find fasta header!")

                headerEnd = chunk.find("\n", headerStart + 1)

                if headerEnd == -1:
                    inFile.close()
                    raise Exception("Incomplete fasta header!")
            
                nextHeader = chunk.find(">", headerEnd + 1)

                if nextHeader == -1:
                    if stop < eof:
                        inFile.seek(start + headerStart)
                        lastFound = headerStart
                        break
                    else:
                        nextHeader = eof - start + 1
        
                header = chunk[headerStart + 1:headerEnd].strip()

                if header not in self._sequences:
                    self._sequences[header] = dict()
                
                self._sequences[header]["indexBegin"] = start + headerEnd + 1
                self._sequences[header]["indexEnd"] = start + nextHeader - 1

                lastFound = nextHeader
    
            start = start + lastFound

            # release the memory
            chunk = None
            startPositions = None
            endPositions = None
            nextPositions = None
        inFile.close()


    def _extractSequence(self, keys=list()):
        try:
            sequenceDict = dict()
            fp = io.open(self._sourceFile, 'r')
            for k in sorted(keys, key=lambda x: self._sequences[x]["indexBegin"]):
                fp.seek(self._sequences[k]["indexBegin"])
                sequenceDict[k] = fp.read(self._sequences[k]["indexEnd"] - self._sequences[k]["indexBegin"]).replace("\n","")
            fp.close()
            return sequenceDict
        except KeyError, e:
            raise KeyError(k)


    def _extractAll(self, func=None):
        inFile = io.open(self._sourceFile, 'r')

        inFile.seek(0, 2)
        bytes = inFile.tell()
        inFile.seek(0)
        contents = inFile.read(bytes)
        inFile.close()

        inFile = None
        eof = None
        
        sequencesDict = dict()

        if func is None:
            headerStart = contents.find(">")
            while headerStart != -1:
                headerEnd = contents.find("\n", headerStart + 1)

                if headerEnd == -1:
                    raise Exception("Incomplete fasta header!")
        
                nextHeader = contents.find(">", headerEnd + 1)

                if nextHeader == -1:
                    nextHeader = len(contents)

                sequencesDict[contents[headerStart + 1:headerEnd].strip()] = \
                    contents[headerEnd + 1:nextHeader - 1].replace("\n","")

                headerStart = contents.find(">", nextHeader)
        else:
            headerStart = contents.find(">")
            while headerStart != -1:
                headerEnd = contents.find("\n", headerStart + 1)

                if headerEnd == -1:
                    raise Exception("Incomplete fasta header!")
        
                nextHeader = contents.find(">", headerEnd + 1)

                if nextHeader == -1:
                    nextHeader = len(contents)
                
                header = contents[headerStart + 1:headerEnd].strip()
                sequencesDict[header] = func(header, contents[headerEnd + 1:nextHeader - 1].replace("\n",""))

                headerStart = contents.find(">", nextHeader)
                
                # free memory
                header = None
                
        return sequencesDict


    
    def getHeaders(self):
        if len(self._sequences) == 0:
            self._extractHeaders()
    
        return self._sequences.keys()

        
    def getSequences(self, keys=list()):
        return self._extractSequence(keys)


    def getAllSequences(self):
        return self._extractAll()
    
            
    def getBioPythonSeqRecordObjects(self, keys=list()):
        sequences = self._extractSequence(keys)
        sequenceObjects = dict()
        
        for x in sequences:
            sequenceObjects[x] = Bio.SeqRecord.SeqRecord(Bio.Seq.Seq(sequences[x], Bio.Alphabet.SingleLetterAlphabet()),
                                                         id=x,
                                                         name=x,
                                                         description=x)
        
        return sequenceObjects
    
    
    def getAllBioPythonSeqRecordObjects(self):
        return self._extractAll(lambda h,s: Bio.SeqRecord.SeqRecord(Bio.Seq.Seq(s, Bio.Alphabet.SingleLetterAlphabet()),
                                                                    id=h,
                                                                    name=h,
                                                                    description=h))


if __name__ == "__main__":
    import datetime
    
    start = datetime.datetime.utcnow()
    f = open("/mnt/search/v5/v5seqfiles/kb|g.140056.fasta", 'r')
    f.seek(0, 2)
    end = f.tell()
    f.seek(0)
    contents = f.read(end)
    f.close()
    end = datetime.datetime.utcnow()
    print "Fastest file read possible took : %s" % str(end - start)
    contents = None

    d = FASTASeqExtractor("/mnt/search/v5/v5seqfiles/kb|g.0.fasta")

    start = datetime.datetime.utcnow()
    # read the whole file and pull out everything as strings
    d.getAllSequences()
    end = datetime.datetime.utcnow()

    print "Reading all sequences as strings took : %s" % str(end - start)

    start = datetime.datetime.utcnow()
    # read the whole file and pull out everything then convert to BioPython SeqRecord objects
    d.getAllBioPythonSeqRecordObjects()
    end = datetime.datetime.utcnow()

    print "Reading all sequences as BioPython SeqRecord Objects took : %s" % str(end - start)

    start = datetime.datetime.utcnow()
    # read the file in chunks and extract just the headers while recording contig start and end
    headers = d.getHeaders()
    end = datetime.datetime.utcnow()
    print "Reading headers and recording contig start and end took : %s" % str(end - start)

    start = datetime.datetime.utcnow()
    # for each key, extract a contig from the file
    for x in headers:
        d.getSequences([x])
    end = datetime.datetime.utcnow()
    print "Reading sequences individually from keys as strings took : %s" % str(end - start)

    start = datetime.datetime.utcnow()
    # get all sequences by passing in all the keys    
    d.getSequences(headers)
    end = datetime.datetime.utcnow()
    print "Reading all sequences using keys as strings took : %s" % str(end - start)


    start = datetime.datetime.utcnow()
    # for each key, get the sequence from the file then make a BioPython SeqRecord object        
    for x in headers:
        d.getBioPythonSeqRecordObjects([x])
    end = datetime.datetime.utcnow()
    print "Reading individual sequences using keys as BioPython SeqRecord Objects took : %s" % str(end - start)

    start = datetime.datetime.utcnow()
    # get all sequences as BioPython SeqRecord Objects by passing in all keys
    records = d.getBioPythonSeqRecordObjects(headers)
    print records.popitem()
    end = datetime.datetime.utcnow()
    print "Reading all sequences as BioPython SeqRecord Objects took : %s" % str(end - start)
