import json
import sys
import random

import biokbase.workspace.client

ws = biokbase.workspace.client.Workspace("http://localhost:7058", user_id='***REMOVED***', password='***REMOVED***')

#ws.create_workspace({'workspace':'test_2','globalread':'n','description':'blah blah blah!'})

json_content = open('83333.2.txt','r').read()

json_object = json.loads(json_content)

for n in xrange(1,10000):

    source_id=random.randint(0,sys.maxint)
    json_object['source_id']=str(source_id)
    metadata = ws.save_objects({'workspace':'test_2','objects':[{'name':source_id,'type':'KBGA.Genome','data':json_object}]})
    print metadata


