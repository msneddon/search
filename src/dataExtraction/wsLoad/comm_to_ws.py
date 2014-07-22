#!/usr/bin/env python

# make mg-rast API calls
# http://api.metagenomics.anl.gov/api.html
# http://api.metagenomics.anl.gov//metagenome?limit=20&verbosity=metadata
# compose objects (all data goes into Metagenome objects)
# add to ws

import datetime
import sys

# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/
reload(sys)
sys.setdefaultencoding("utf-8")

import simplejson
import time
import random
import requests
import re

#import biokbase.cdmi.client
import biokbase.workspace.client

communities_api_url = "http://kbase.us/services/communities/"

# set to small number for testing
max_num_metagenomes = 10E7

skip_existing = False

def extractValues(d):
    # would want to handle more types (e.g., int, float, list)
    values = [x for x in d.values() if type(x) in [str, unicode]]
    #print >> sys.stderr, values

    for x in d.values():
        #print >> sys.stderr, type(x)
        if type(x) == dict:
            #print >> sys.stderr, x
            subvalues = extractValues(x)
            values.extend(subvalues)
    return values
    
def load_ws_metagenomes(mg_list,ws,wsname):

    content = mg_list.json()
    
# would like the equivalent of a do-while loop here
    if content.has_key('next'):
        pass
    else:
        content['next'] = True

    mg_counter = 0
    mg_valid = 0
    
    while content.has_key('next'):        
        #print >> sys.stderr, mg_list.status_code
        #print >> sys.stderr, mg_list.headers
    
        #print >> sys.stderr,  content['data'][0]['library'][1]
        #sys.exit(0)
    
        # possible test: if one mg given, stuff it into content['data']
        items = list()
        if content.has_key('data'):
            items = content['data']
        else:
            items = [ content ]
    #    print >> sys.stderr, items
        
        failed_items = list()
    
        ws_object_list = list()
        for mg_item in items:
            #print mg_item
        
            mg_id = mg_item['id']
            sample_id = mg_item['sample'][0]
            project_id = mg_item['project'][0]
            library_id = mg_item['library'][0]
            ws_obj_name = mg_id
    
            #print >> sys.stderr, mg_id, sample_id, project_id, library_id
    
            # possible feature: skip metagenomes that are already loaded
            # need to update if changing how stored
            try:
                ws.get_object_info([{"workspace": wsname,"name": ws_obj_name}],0)
                if skip_existing == True:
                    print >> sys.stderr, 'object '  + ws_obj_name + ' found, skipping'
                    mg_counter += 1
                    continue
                print >> sys.stderr, 'object '  + ws_obj_name + ' found, to be updated'
                mg_valid += 1
            except biokbase.workspace.client.ServerError:
                print >> sys.stderr, 'object '  + ws_obj_name + ' not found, adding'
        
            ws_object = dict()
    
            # skip this metagenome if it does not have a library associated with it
            try:
                mg_library_response = requests.get(communities_api_url + 'library/' + library_id + '?verbosity=full')
                mg_library = mg_library_response.json()
                
                if mg_library.has_key("ERROR"):
                    raise Exception(mg_library)
            except Exception, e:
                print >> sys.stderr, 'skipping, exception retrieving library ' + library_id + ' for metagenome ' + mg_id
                print >> sys.stderr, e.message
                failed_items.append((mg_item, e))
                continue
            #else:
            #    print >> sys.stderr, 'skipping, bad library_id ' + library_id + ' for metagenome ' + mg_id
            #    failed_items.append((mg_item, "library_id error"))
            #    continue
        
            # skip this metagenome if it does not have a project associated with it
            #if type(project_id) == type(str) and project_id.find("mgp") > -1:
            try:
                mg_project_response = requests.get(communities_api_url + 'project/' + project_id + '?verbosity=full')
                mg_project = mg_project_response.json()
                
                if mg_project.has_key("ERROR"):
                    raise Exception(mg_project)
            except Exception, e:
                print >> sys.stderr, 'skipping, exception retrieving project ' + project_id + ' for metagenome ' + mg_id
                print >> sys.stderr, e.message
                failed_items.append((mg_item, e))
                continue
            #else:
            #    print >> sys.stderr, 'skipping, error retrieving project ' + project_id + ' for metagenome ' + mg_id
            #    failed_items.append((mg_item, "project_id error"))
            #    continue
        
            # skip this metagenome if it does not have a sample associated with it
            #if type(sample_id) == type(str) and sample_id.find("mgs") > -1:
            try:
                mg_sample_response = requests.get(communities_api_url + 'sample/' + sample_id + '?verbosity=full')
                mg_sample = mg_sample_response.json()
                
                if mg_sample.has_key("ERROR"):
                    raise Exception(mg_sample)
            except Exception, e:
                print >> sys.stderr, 'skipping, exception retrieving sample ' + sample_id + ' for metagenome ' + mg_id
                print >> sys.stderr, e.message
                failed_items.append((mg_item, e))
                continue
            #else:
            #    print >> sys.stderr, 'skipping, error retrieving sample ' + sample_id + ' for metagenome ' + mg_id
            #    failed_items.append((mg_item, "sample_id error"))
            #    continue
    
            # skip this metagenome if mixs information cannot be obtained    
            try:
                mg_mixs_response = requests.get(communities_api_url + 'metagenome/' + mg_id + '?verbosity=mixs')
                mg_mixs = mg_mixs_response.json()
                
                if mg_mixs.has_key("ERROR"):
                    raise Exception(mg_mixs)
            except Exception, e:
                print >> sys.stderr, 'skipping, exception retrieving mixs ' + mg_id + ' for metagenome ' + mg_id
                print >> sys.stderr, e.message
                failed_items.append((mg_item, e))
                continue
        
            ws_object['metagenome_id'] = mg_item['id']
            ws_object['metagenome_name'] = mg_item['name']
            ws_object['metagenome_url'] = mg_item['url']
            ws_object['sequence_type'] = mg_item['sequence_type']
            ws_object['seq_method'] = mg_mixs['seq_method']
            #ws_object['created'] = mg_item['created']
            ws_object['library_id'] = mg_item['library'][0]
            ws_object['library_url'] = mg_item['library'][1]
            #ws_object['metadata'] = mg_item['metadata']
        
            pat = re.compile(r'\s+')
            ws_object['metadata'] = dict()
    
            try:
                # need to use extractValues here to make it look right
                for metadata_key in mg_item['metadata']:
                    ws_object['metadata'][metadata_key] = ' '.join(extractValues((mg_item['metadata'][metadata_key])))
                metagenome_keys = ['sequence_type','created']
                for metagenome_key in metagenome_keys:
                    if mg_item.has_key(metagenome_key):
                        ws_object[metagenome_key] = mg_item[metagenome_key]
            except Exception, e:
                print >> sys.stderr, mg_item
                print >> sys.stderr, e
    
            # created: "2008-06-18 14:03:02",
            ws_object['created'] = datetime.datetime.isoformat(datetime.datetime.strptime(mg_item['created'], "%Y-%m-%d %H:%M:%S")) + 'Z'
        
            ws_object['sequence_download_urls'] = list()
            if mg_library.has_key('sequence_sets'):
                ws_object['sequence_download_urls'] = [ x['url'] for x in mg_library['sequence_sets'] ]
        
            ws_object['sample'] = dict()
            ws_object['sample']['sample_id'] = mg_sample['id']
            ws_object['sample']['sample_name'] = mg_sample['name']
            ws_object['sample']['sample_url'] = mg_sample['url']
            ws_object['sample']['created'] = datetime.datetime.isoformat(datetime.datetime.strptime(mg_sample['created'], "%Y-%m-%d %H:%M:%S")) + 'Z'
        
            mixs_keys = ['env_package_type','feature','biome','material','location','country']
            for mixs_key in mixs_keys:
                if mg_mixs.has_key(mixs_key):
                    ws_object['sample'][mixs_key] = mg_mixs[mixs_key]
            mixs_float_keys = ['latitude','longitude']
            for mixs_key in mixs_float_keys:
                if mg_mixs.has_key(mixs_key) and mg_mixs[mixs_key] != '':
                    try:
                        ws_object['sample'][mixs_key] = float(mg_mixs[mixs_key])
                    except Exception, e:
                        print >> sys.stderr, e
    
            # parse the original collection date string and try to make it ISO8601 compliant in UTC/GMT time    
            try:
                # clear leading and ending whitespace
                dateString = str(mg_mixs['collection_date']).strip()
    
                # if the string is empty we are done
                if len(dateString) == 0:
                    ws_object['sample']['collection_date'] = ""
                elif dateString.find("UTC") > 0:
                    print >> sys.stderr, "found UTC"
    
                    # split the string to determine the right datetime format to parse with                
                    dateParts = dateString.split(' ')
                    print >> sys.stderr, dateParts
    
                    # UTC offset in hours and minutes
                    offsetHours = 0
                    offsetMinutes = 0
    
                    # parse the UTC offset
#                    if len(dateParts) == 4 or dateParts[-1].find("UTC-") > 0 or dateParts[-1].find("UTC+") > 0:
                    if len(dateParts) == 4 or 'UTC-' in dateParts[-1] or 'UTC+' in dateParts[-1]:
                        print >> sys.stderr, "UTC offset " + dateString
    
                        # strip off the UTC offset to keep the time format selection consistent
                        dateParts = dateParts[:-1]
                        
                        offset = int(dateString.split("UTC")[1].strip())
                        if abs(offset) < 24:
                            offsetHours = offset
                            offsetMinutes = 0
                        else:
                            offsetHours = offset / 1000
                            offsetMinutes = offset % 1000
                        
                        dateString = dateString[:dateString.find("UTC") + 3]

                    print >> sys.stderr, offsetHours, offsetMinutes, dateString
                    print >> sys.stderr, dateParts
    
                    # choose the correct timeFormatString
                    timeFormatString = ""
                    # a time was found
                    if len(dateParts) == 3:                    
                        timeFormatString = "%Y-%m-%d %H:%M:%S %Z"
                    if len(dateParts) == 2:                    
                        timeFormatString = "%Y-%m-%d %H:%M:%S %Z"
                        if (dateParts[-1] == 'UTC'):
                            timeFormatString = "%Y-%m-%d %Z"
                    # neither a time nor a UTC offset was found
                    elif len(dateParts) == 1:
                        timeFormatString = "%Y-%m-%d %Z"
                    # no time was found, but a real UTC offset was
                    elif len(dateParts) == 0:
                        timeFormatString = "%Y-%m-%d %Z"
#                        if 'UTC-' in dateParts[-1] or 'UTC+' in dateParts[-1]:
#                            timeFormatString = "%Y-%m-%d %Z%z"
    
                    print >> sys.stderr, timeFormatString
    
                    # parse the date string, apply the offset, convert to ISO8601
                    collection_date = datetime.datetime.strptime(dateString, timeFormatString)
                    # if there is a time given, convert it
                    if len(dateParts) == 3:
                        collection_date += datetime.timedelta(hours = offsetHours, minutes = offsetMinutes)
                    dateString = datetime.datetime.isoformat(collection_date) + "Z"
                        
                    print >> sys.stderr, 'collection_date: ' + mg_mixs['collection_date']
                    print >> sys.stderr, 'dateString: ' + dateString
    
                    ws_object['sample']['collection_date'] = dateString
                else:
                    print >> sys.stderr, 'unknown collection_date format ' + str(mg_mixs['collection_date'])
                    ws_object['sample']['collection_date'] = mg_mixs['collection_date']
            except Exception, e:
                ws_object['sample']['collection_date'] = mg_mixs['collection_date']            
                print >> sys.stderr, ' unexpected error with collection_date ' + str(mg_mixs['collection_date'])
                print >> sys.stderr, str(e)
    
            sample_keys = ['version','metadata']
            for sample_key in sample_keys:
                if mg_sample.has_key(sample_key):
                    ws_object['sample'][sample_key] = mg_sample[sample_key]
        
            if mg_sample.has_key('project'):
                ws_object['sample']['project'] = mg_sample['project'][0]
    
            try:    
                ws_object['project'] = dict()
                ws_object['project']['project_id'] = mg_project['id']
                ws_object['project']['project_name'] = mg_project['name']
                ws_object['project']['project_description'] = mg_project['description']
                ws_object['project']['project_url'] = mg_project['url']
            except Exception, e:
                print >> sys.stderr, e
                print >> sys.stderr, mg_project
    
            try:
                dateString = str(mg_project['created']).strip()
    
                if len(dateString) == 0:
                    ws_object['project']['created'] = ""
                elif len(dateString.split(' ')) == 3:
                    ws_object['project']['created'] = datetime.datetime.isoformat(datetime.datetime.strptime(mg_project['created'], "%Y-%m-%d %H:%M:%S %Z")) + "Z"
                else:
                    ws_object['project']['created'] = datetime.datetime.isoformat(datetime.datetime.strptime(mg_project['created'], "%Y-%m-%d %Z")) + "Z"
    
                print >> sys.stderr, mg_project['created'], ws_object['project']['created']
            except Exception, e:
                print >> sys.stderr, e
        
            try:
                project_keys = ['funding_source']
                for project_key in project_keys:
                    if mg_project.has_key(project_key):
                        ws_object['project'][project_key] = str(mg_project[project_key])
        
                ws_object['project']['samples'] = [x[0] for x in mg_project['samples']]
        
                ws_object['project']['PI_info'] = dict()
                ws_object['project']['PI_info']['email'] = ''
    
                if mg_project['metadata'].has_key('PI_email'):
                    ws_object['project']['PI_info']['email'] = mg_project['metadata']['PI_email']
    
                ws_object['project']['PI_info']['last_name'] = ''
                if mg_project['metadata'].has_key('PI_lastname'):
                    ws_object['project']['PI_info']['last_name'] = mg_project['metadata']['PI_lastname']
    
                ws_object['project']['PI_info']['first_name'] = ''
                if mg_project['metadata'].has_key('PI_firstname'):
                    ws_object['project']['PI_info']['first_name'] = mg_project['metadata']['PI_firstname']
    
                ws_object['project']['PI_info']['organization'] = ''
                if mg_project['metadata'].has_key('PI_organization'):
                    ws_object['project']['PI_info']['organization'] = mg_project['metadata']['PI_organization']
    
                ws_object['project']['PI_info']['address'] = ''
                if mg_project['metadata'].has_key('PI_organization_address'):
                    ws_object['project']['PI_info']['address'] = mg_project['metadata']['PI_organization_address']
        
    
                ws_object['project']['tech_contact'] = dict()
                ws_object['project']['tech_contact']['email'] = ''
    
                if mg_project['metadata'].has_key('email'):
                    ws_object['project']['tech_contact']['email'] = mg_project['metadata']['email']
    
                ws_object['project']['tech_contact']['last_name'] = ''
                if mg_project['metadata'].has_key('lastname'):
                    ws_object['project']['tech_contact']['last_name'] = mg_project['metadata']['lastname']
    
                ws_object['project']['tech_contact']['first_name'] = ''
                if mg_project['metadata'].has_key('firstname'):
                    ws_object['project']['tech_contact']['first_name'] = mg_project['metadata']['firstname']
    
                ws_object['project']['tech_contact']['organization'] = ''
                if mg_project['metadata'].has_key('organization'):
                    ws_object['project']['tech_contact']['organization'] = mg_project['metadata']['organization']
    
                ws_object['project']['tech_contact']['address'] = ''
                if mg_project['metadata'].has_key('organization_address'):
                    ws_object['project']['tech_contact']['address'] = mg_project['metadata']['organization_address']
            except Exception, e:
                print >> sys.stderr, "Unexpected error processing project information: ", e
                print >> sys.stderr, mg_project
        
            ws_object_list.append({"type":"KBaseCommunities.Metagenome","data":ws_object,"name":ws_obj_name})
    
            #print simplejson.dumps(ws_object, sort_keys=True, indent="    ")
    
            mg_counter += 1
            mg_valid += 1

        #print simplejson.dumps(ws_object_list,sort_keys=True,indent=4 * ' ')
        
        if len(ws_object_list) > 0:
            try:
                wsobj_info = ws.save_objects({"workspace":wsname,"objects":ws_object_list})
                print >> sys.stderr, "Managed to save these objects: " + str(ws_object_list)
            except Exception, e:
                print >> sys.stderr, ws_object_list
                print >> sys.stderr, "Unable to save objects!"
                print >> sys.stderr, e
    
                f = open('failed.txt', 'w')
                f.write(simplejson.dumps(failed_items))
                f.close()
                sys.exit(0)
            
#            print >> sys.stderr, wsobj_info
        else:
            print >> sys.stderr, 'no objects in this set, moving to next set'
    
        if mg_counter >= max_num_metagenomes:
            print "examined at least " + str(max_num_metagenomes) + ", all done"
            return True
        
        mg_list = requests.get(content['next'])
        content = mg_list.json()
    
        print "Valid mg : " + str(mg_valid)

if __name__ == "__main__":
    import argparse
    import os.path

    batch_size = 100

    parser = argparse.ArgumentParser(description='Create workspace objects from metagenomics API.')
    parser.add_argument('--wsname', nargs=1, help='workspace name to use', required=True)
    parser.add_argument('--skip-existing',action='store_true',help='skip processing metagenomes which already exist in ws')
    parser.add_argument('--debug',action='store_true',help='debugging (currently use dev workspace instead of pub)')
    parser.add_argument('--max-num',nargs=1,type=int,help='maximum number of objects to attempt to load (default ' + str(max_num_metagenomes) + ')')
    parser.add_argument('--batch-size',nargs=1,type=int,help='number of metagenomes to fetch at a time (default ' + str(batch_size) + ')')
    parser.add_argument('metagenomes', nargs='*', help='metagenomes to load (default all, currently only one arg works) (currently not working)')

    args = parser.parse_args()

    wsname = args.wsname[0]

    ws = biokbase.workspace.client.Workspace("https://kbase.us/services/ws")
    # ws team dev instance
    if args.debug:
#        ws = biokbase.workspace.client.Workspace("http://140.221.84.209:7058", user_id='***REMOVED***', password='***REMOVED***')
        ws = biokbase.workspace.client.Workspace("http://dev04:7058", user_id='***REMOVED***', password='***REMOVED***')

    if args.max_num:
        max_num_metagenomes=args.max_num[0]

    if args.batch_size:
        batch_size = args.batch_size[0]

    if args.skip_existing:
        skip_existing = True

    wsdesc = 'Workspace for communities objects for searching'

    try:
        retval=ws.create_workspace({"workspace":wsname,"globalread":"n","description":wsdesc})
        print >> sys.stderr, 'created workspace ' + wsname + ' at ws url ' + ws.url
        print >> sys.stderr, retval
    # ideally want this to catch only workspace exists errors
    except biokbase.workspace.client.ServerError, e:
        print >> sys.stderr, 'workspace ' + wsname + ' at ws url ' + ws.url + ' may already exist, trying to use'

    #mg_list = requests.get(communities_api_url + 'metagenome?limit=20&verbosity=full')
    # try verbosity=metadata
    mg_list = []

    if len(args.metagenomes) > 0:
        print >> sys.stderr, 'found metagenomes on command line, using first'
        mg_list = requests.get(communities_api_url + 'metagenome/' + args.metagenomes[0])
        max_num_metagenomes = 1
    else:
        mg_list = requests.get(communities_api_url + 'metagenome?verbosity=metadata&limit=' + str(batch_size) )

    load_ws_metagenomes(mg_list,ws,wsname)
