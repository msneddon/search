'''
Created on May 17, 2013

@author: crusherofheads
'''
from ConfigParser import ConfigParser
import sys
import urllib
import json
from deep_eq import deep_eq

config = ConfigParser()
config.read('../test.cfg')

baseurl = None
for k, v in config.items('search'):
    if k == 'core_url':
        baseurl = v
        break

if not baseurl:
    print 'No core_url param in config file ../test.cfg'
    sys.exit(1)

def get_response(url):
    return json.loads(urllib.urlopen(baseurl + url).read())

print 'test no input'
resp = get_response('?')

# TODO alter test when proper error responses available

# TODO assert False until test fixed

#deep_eq(resp, expected, _assert=True)

print 'test misspelled target'
resp = get_response('Genme/coli')

# TODO alter test when proper error responses available

# TODO assert False until test fixed

#deep_eq(resp, expected, _assert=True)

print 'test string for start'
resp = get_response('Genome/coli?start=foo')

# TODO alter test when proper error responses available

# TODO assert False until test fixed

#deep_eq(resp, expected, _assert=True)

print 'test string for count'
resp = get_response('Genome/coli?count=foo')

# TODO alter test when proper error responses available

# TODO assert False until test fixed

#deep_eq(resp, expected, _assert=True)

print 'test borked param string with #'
resp = get_response('Genome/coli#count=1')

# TODO alter test when proper error responses available

# TODO assert False until test fixed

#deep_eq(resp, expected, _assert=True)

print 'test borked param string 2 x ?'
resp = get_response('Genome/coli?count=1?start=3')

# TODO alter test when proper error responses available

# TODO assert False until test fixed

#deep_eq(resp, expected, _assert=True)

print 'test borked param string start with &'
resp = get_response('Genome/coli&count=1')

# TODO alter test when proper error responses available

# TODO assert False until test fixed

#deep_eq(resp, expected, _assert=True)

print 'test borked param string ask for bad format'
resp = get_response('Genome/coli?count=1&format=yaml')

# TODO alter test when proper error responses available

# TODO assert False until test fixed

#deep_eq(resp, expected, _assert=True)



print resp  
