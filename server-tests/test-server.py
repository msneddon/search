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

assert 'version' in resp

del resp['version']

expected = {u'status': 200,
            u'service':
            u'KBase Search Service - Check out www.kbase.us for usage info'}

deep_eq(resp, expected, _assert=True)


