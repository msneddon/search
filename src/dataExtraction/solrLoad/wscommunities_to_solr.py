#!/usr/bin/env python
 
import StringIO 
import simplejson 
import sys 
import random 
import re 
import pprint
import datetime
 
# found at https://pythonadventures.wordpress.com/tag/unicodeencodeerror/    
reload(sys)
sys.setdefaultencoding("utf-8") 

import biokbase.workspace.client 

pp = pprint.PrettyPrinter(indent=4)


#Metagenome ws object gets all values up and including pipeline columns
#Tax Profiles get ['object_id', 'object_type', 'object_workspace', 'object_name', 'metagenome_id','metagenome_name','tax_leaf','tax_level','tax_level_description','tax_abundance','tax_evalue','tax_percent_id','tax_alignment_length','tax_lineage'] columns
#Func Profiles get ['object_id', 'object_type', 'object_workspace', 'object_name', 'metagenome_id','metagenome_name','func_leaf','func_level','func_level_description','func_abundance','func_evalue','func_percent_id','func_alignment_length','func_lineage'] columns
 
solr_keys = ['object_id', 'object_type', 'object_workspace', 'object_name', 'metagenome_id', 'metagenome_name', 'sequence_type', 'metagenome_created','project_id','project_url','mixs_compliant','mix_env_package_type','mix_country','mix_location','mix_latitude','mix_longitude','mix_PI_firstname','mix_PI_lastname','mix_sequence_type','mix_seq_method','mix_collection_date','mix_feature','mix_biome','mix_project_name','mix_project_id','mix_material','ss_average_ambig_chars_raw','ss_read_count_annotated','ss_ratio_reads_rna','ss_ambig_sequence_count_raw','ss_alpha_diversity_shannon','ss_standard_deviation_gc_ratio_raw','ss_drisee_score_raw','ss_standard_deviation_gc_ratio_preprocessed','ss_sequence_count_processed_rna','ss_length_min_preprocessed_rna','ss_sequence_count_preprocessed','ss_read_count_processed_rna','ss_average_length_preprocessed','ss_average_gc_ratio_preprocessed','ss_average_ambig_chars_preprocessed','ss_average_length_raw','ss_ambig_sequence_count_preprocessed_rna','ss_average_gc_ratio_preprocessed_rna','ss_cluster_count_processed_aa','ss_length_max_preprocessed_rna','ss_ambig_char_count_raw','ss_average_length_preprocessed_rna','ss_standard_deviation_length_raw','ss_average_gc_content_preprocessed','ss_sequence_count_sims_rna','ss_sequence_count_dereplication_removed','ss_read_count_processed_aa','ss_bp_count_preprocessed','ss_standard_deviation_gc_content_raw','ss_bp_count_raw','ss_standard_deviation_gc_ratio_preprocessed_rna','ss_average_ambig_chars_preprocessed_rna','ss_cluster_count_processed_rna','ss_standard_deviation_length_preprocessed_rna','ss_clustered_sequence_count_processed_rna','ss_ratio_reads_aa','ss_sequence_count_preprocessed_rna','ss_sequence_count_ontology','ss_sequence_count_raw','ss_clustered_sequence_count_processed_aa','ss_average_gc_ratio_raw','ss_average_gc_content_raw','ss_standard_deviation_gc_content_preprocessed_rna','ss_sequence_count_sims_aa','ss_ambig_char_count_preprocessed_rna','ss_bp_count_preprocessed_rna','ss_standard_deviation_length_preprocessed','ss_standard_deviation_gc_content_preprocessed','ss_average_gc_content_preprocessed_rna','ss_ambig_char_count_preprocessed','ss_ambig_sequence_count_preprocessed','pipeline_version','pipeline_assembled','pipeline_rna_pid','pipeline_fgs_type','pipeline_filter_ambig','pipeline_prefix_length','pipeline_aa_pid','pipeline_publish_priority','pipeline_m5nr_sims_version','pipeline_m5nr_annotation_version','pipeline_filter_ln','pipeline_m5rna_annotation_version','pipeline_file_type','pipeline_m5rna_sims_version','pipeline_max_ambig','pipeline_bowtie','pipeline_filter_ln_mult','pipeline_dereplicate','pipeline_screen_indexes','tax_leaf','tax_level','tax_level_description','tax_abundance','tax_evalue','tax_percent_id','tax_alignment_length','tax_lineage','func_leaf','func_level','func_level_description','func_abundance','func_evalue','func_percent_id','func_alignment_length','func_lineage']


#LEAF AS True or False

def get_profile_grouping_info(profile, row_metadata_key):
    data_rows = profile["data"]["data"]
    rows = profile["data"]["rows"] 
    columns = profile["data"]["columns"] 
    
    abundance_index = -1 
    e_value_index = -1 
    percent_identity_index = -1
    alignment_length_index = -1
    metagenome_set = set()
 
    for column_counter in range(len(columns)):
        column = columns[column_counter]
        if (column.has_key("metadata") and column["metadata"].has_key("metagenome")):
            metagenome_set.add(column["metadata"]["metagenome"]) 
        if column.has_key("id"): 
            col_id = column["id"]
            if col_id == "abundance": 
                abundance_index = column_counter 
            if col_id == "e-value":
                e_value_index = column_counter 
            if col_id == "percent identity": 
                percent_identity_index = column_counter
            if col_id == "alignment length": 
                alignment_length_index = column_counter

    if len(metagenome_set) != 1: 
        print "ERROR :Either Zero or More than one metagenome for object : "+  str(x[0])
        sys.exit(0)
    if abundance_index == -1:
        print "ERROR :Profile has no abundance : "+  str(x[0])
        sys.exit(0) 

    metagenome_ref = ""
    metagenomes = profile["metagenomes"]["elements"]
    if len(metagenomes) != 1: 
        print "ERROR :Either Zero or More than one metagenome for object : "+  str(x[0]) 
        sys.exit(0) 
    for metagenome in metagenomes.keys():
        metagenome_ref = metagenomes[metagenome]["ref"]
 
    total_abundance = 0 
 
    #triple layer Dict where top level key is the numeric value of the level it is on.
    #the second dict is the name of the level (tax name or ontology)   
    # value is a dict with .  has keys {is_leaf, abundance, lineage, e_value, percent_identity, alignment}
    level_name_abundance_dict = dict() 
    total_row_count = len(rows)
 
    for row_counter in range(total_row_count):
        #NEW ROW                              
        total_abundance = total_abundance + data_rows[row_counter][abundance_index]
        row = rows[row_counter]
#        row_levels = row["metadata"]["taxonomy"] for taxonomic profile
#        row_levels = row["metadata"]["ontology"] for functional profile
        row_levels = row["metadata"][row_metadata_key]
        row_id = row["id"] 
        
        total_row_level_count = len(row_levels)
    
        if (total_row_level_count > 0) and (row_levels[-1] != row_id):
            #get lineage, e-Value, percent_id, alignment_length                   
            lineage = ":".join(row_levels) + ":" + row_id
            if e_value_index != -1 :
                e_value = data_rows[row_counter][e_value_index]
            else: 
                e_value = "" 
            if percent_identity_index != -1 : 
                percent_identity = data_rows[row_counter][percent_identity_index]
            else:
                percent_identity = ""
            if alignment_length_index != -1:
                alignment_length = data_rows[row_counter][alignment_length_index]
            else: 
                alignment_length = ""
 
            if (level_name_abundance_dict.has_key(total_row_level_count)): 
                level_name_abundance_dict[total_row_level_count][row_id] = {"is_leaf":True,"abundance":data_rows[row_counter][abundance_index],"lineage":lineage,"e_value":e_value,"percent_identity":percent_identity,"alignment":alignment_length} 
            else: 
                level_name_abundance_dict[total_row_level_count]= {row_id:{"is_leaf":True,"abundance":data_rows[row_counter][abundance_index],"lineage":lineage,"e_value":e_value,"percent_identity":percent_identity,"alignment":alignment_length}} 
 
 
#            print "TOTAL ROW LEVEL COUNT : " + str(total_row_level_count)  
        for level_number in range(total_row_level_count):
#                print "Level number : " + str(level_number)   
#                print "Name : " + row_levels[level_number] 
            name = row_levels[level_number]
            is_leaf = False 
            lineage = "" 
            e_value = ""
            percent_identity = "" 
            alignment_length = "" 
 
            if (level_name_abundance_dict.has_key(level_number) and level_name_abundance_dict[level_number].has_key(name) and level_name_abundance_dict[level_number][name].has_key("abundance")): 
                new_abundance = level_name_abundance_dict[level_number][name]["abundance"] + data_rows[row_counter][abundance_index] 
            else: 
                new_abundance = data_rows[row_counter][abundance_index] 
            if ((level_number == (total_row_level_count - 1)) and (name == row_id)): 
                is_leaf = True 
                #get lineage, e-Value, percent_id, alignment_length 
                lineage = ":".join(row_levels) 
                if e_value_index != -1 : 
                    e_value = data_rows[row_counter][e_value_index] 
                if percent_identity_index != -1 : 
                    percent_identity = data_rows[row_counter][percent_identity_index] 
                if alignment_length_index != -1: 
                    alignment_length = data_rows[row_counter][alignment_length_index] 
 
            if level_name_abundance_dict.has_key(level_number): 
                level_name_abundance_dict[level_number][name] = {"is_leaf":is_leaf,"abundance":new_abundance,"lineage":lineage,"e_value":e_value,"percent_identity":percent_identity,"alignment":alignment_length} 
            else: 
                level_name_abundance_dict[level_number]= {name:{"is_leaf":is_leaf,"abundance":new_abundance,"lineage":lineage,"e_value":e_value,"percent_identity":percent_identity,"alignment":alignment_length}} 
    
    #ADD RETURN STATEMENT  return list that is metagenome_ref, total_abundance, level_name_abundance_dict
    return_list = [ metagenome_ref, total_abundance, level_name_abundance_dict]
    return return_list
            

def export_communities_from_ws(maxNumObjects, metagenome_list, wsname):
    # gavin's dev instance
#    ws_client = biokbase.workspace.client.Workspace('http://dev04:7058')
    # production instance 
    ws_client = biokbase.workspace.client.Workspace('https://kbase.us/services/ws') 
 
    workspace_object = ws_client.get_workspace_info({'workspace':wsname})  
    all_workspaces = [ workspace_object ] 

    headerOutFile = open('communitiesToSolr.tab.headers', 'w') 
    print >> headerOutFile, "\t".join(solr_keys) 
    #print >> headerOutFile, "\n"                                                                                                                
    headerOutFile.close() 

    outFile = open('communitiesToSolr.tab', 'w')

    #NEED TO DO BECAUSE THE DO NOT STORE IDS PROPERLY IN THE PROFILES
    #Key is metagenome_id (What is stored in the profiles), the value is a list [name, id] of the metagenome (Note not ws_object_name, ws_obj_id)
    metagenome_id_name_dict = dict()

    workspace_counter = 0
    for n in all_workspaces: 
        workspace_id = n[0]
        workspace_name = n[1] 
#Info Log 
        print metagenome_list 
        objects_list = list() 
        if len(metagenome_list) > 0: 
            names_list = list() 
            for metagenome in metagenome_list: 
                names_list.append({'workspace':wsname,'name':metagenome}) 
            objects_list = [x['info'] for x in ws_client.get_objects(names_list)] 
        else: 
# to do: need to make a few calls to list_objects to capture all of them
            object_count = 1 
            skipNum = 0 
            limitNum = 5000 
            while object_count != 0: 
                this_list = ws_client.list_objects({"ids": [workspace_id],"type":"Communities.Metagenome","limit":limitNum,"skip":skipNum}) 
                object_count=len(this_list) 
                skipNum += limitNum 
                objects_list.extend(this_list) 
 
        objects_list.sort() 

        if len(objects_list) > 0:
#Info Log
            print "\tWorkspace %s has %d matching objects" % (workspace_name, len(objects_list))
            object_counter = 0
 
            if maxNumObjects < 1000: 
                objects_list = random.sample(objects_list,maxNumObjects) 

            counter = 0
            for x in objects_list: 
#Info log 
#                print "\t\tChecking %s, done with %s of all objects in %s" % (x[1], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name) 
                if "Metagenome" in x[2]:
                    done = False
                    while not done:
                        try: 
                            metagenome = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}]) 
                            done = True 
                        except Exception, e: 
#Error Log                                                                                                               
                            print str(e) 
                            print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id) 
                    metagenome = metagenome[0] 
#                    print metagenome['data'].keys()                                                                            

                    metagenome_object = dict() 
                    for x in solr_keys: 
                        metagenome_object[x] = "" 

                    metagenome_object['object_id'] = 'kb|ws.' + str(metagenome['info'][6]) + '.obj.' + str(metagenome['info'][0]) 
                    metagenome_object['object_workspace'] = metagenome['info'][7] 
                    metagenome_object['object_type'] = metagenome['info'][2] 
                    metagenome_object['object_name'] = metagenome['info'][1] 

                    ws_object_id = str(metagenome['info'][0])
                    ws_id = str(metagenome['info'][6])
                    ws_object_version = str(metagenome['info'][4])
                    metagenome_object_ref_key = ws_id + "/" + ws_object_id + "/" + ws_object_version


                    metagenome_object["metagenome_id"] = metagenome['data']['id']
                    metagenome_object["metagenome_name"] = metagenome['data']['name']

                    metagenome_id_name_dict[metagenome_object_ref_key] = [metagenome_object["metagenome_id"],metagenome_object["metagenome_name"]]

                    if metagenome['data'].has_key('sequence_type'):
                        metagenome_object["sequence_type"] = metagenome['data']['sequence_type']

                    if metagenome['data'].has_key('created'):
                        metagenome_object["metagenome_created"] = metagenome['data']['created']

                    if metagenome['data'].has_key('project'):
                        project_list =  metagenome['data']['project']
                        if (len(project_list) == 2):
                            metagenome_object["project_id"]= project_list[0]
                            metagenome_object["project_url"]= project_list[1]

                    if metagenome['data'].has_key('mixs_compliant'):
                        metagenome_object["mixs_compliant"] = metagenome['data']['mixs_compliant']     

                    #MIXS PORTION
                    if metagenome['data'].has_key('mixs'):
                        mixs_dict = metagenome['data']['mixs']
                        if mixs_dict.has_key('env_package_type'): 
                            metagenome_object["mix_env_package_type"] = mixs_dict['env_package_type'] 

                        if mixs_dict.has_key('country'): 
                            metagenome_object["mix_country"] = mixs_dict['country'] 

                        if mixs_dict.has_key('location'): 
                            metagenome_object["mix_location"] = mixs_dict['location'] 

                        if mixs_dict.has_key('latitude'): 
                            metagenome_object["mix_latitude"] = mixs_dict['latitude'] 

                        if mixs_dict.has_key('longitude'): 
                            metagenome_object["mix_longitude"] = mixs_dict['longitude'] 

                        if mixs_dict.has_key('PI_firstname'): 
                            metagenome_object["mix_PI_firstname"] = mixs_dict['PI_firstname'] 

                        if mixs_dict.has_key('PI_lastname'): 
                            metagenome_object["mix_PI_lastname"] = mixs_dict['PI_lastname'] 

                        if mixs_dict.has_key('sequence_type'): 
                            metagenome_object["mix_sequence_type"] = mixs_dict['sequence_type'] 

                        if mixs_dict.has_key('seq_method'): 
                            metagenome_object["mix_seq_method"] = mixs_dict['seq_method'] 

                        if mixs_dict.has_key('collection_date'): 
                            metagenome_object["mix_collection_date"] = mixs_dict['collection_date'] 

                        if mixs_dict.has_key('feature'): 
                            metagenome_object["mix_feature"] = mixs_dict['feature'] 

                        if mixs_dict.has_key('biome'): 
                            metagenome_object["mix_biome"] = mixs_dict['biome'] 

                        if mixs_dict.has_key('project_name'): 
                            metagenome_object["mix_project_name"] = mixs_dict['project_name'] 

                        if mixs_dict.has_key('project_id'): 
                            metagenome_object["mix_project_id"] = mixs_dict['project_id'] 

                        if mixs_dict.has_key('material'): 
                            metagenome_object["mix_material"] = mixs_dict['material'] 

                    #SEQUENCE STATS PORTION
                    if ((metagenome['data'].has_key('statistics')) and (metagenome['data']['statistics'].has_key('sequence_stats'))):
                        ss_dict = metagenome['data']['statistics']['sequence_stats']
                        metagenome_object['ss_average_ambig_chars_raw'] = ss_dict["average_ambig_chars_raw"] if ss_dict.has_key("average_ambig_chars_raw") else ""
                        metagenome_object['ss_read_count_annotated'] = ss_dict["read_count_annotated"] if ss_dict.has_key("read_count_annotated") else ""
                        metagenome_object['ss_ratio_reads_rna'] = ss_dict["ratio_reads_rna"] if ss_dict.has_key("ratio_reads_rna") else ""
                        metagenome_object['ss_ambig_sequence_count_raw'] = ss_dict["ambig_sequence_count_raw"] if ss_dict.has_key("ambig_sequence_count_raw") else ""
                        metagenome_object['ss_alpha_diversity_shannon'] = ss_dict["alpha_diversity_shannon"] if ss_dict.has_key("alpha_diversity_shannon") else ""
                        metagenome_object['ss_standard_deviation_gc_ratio_raw'] = ss_dict["standard_deviation_gc_ratio_raw"] if ss_dict.has_key("standard_deviation_gc_ratio_raw") else ""
                        metagenome_object['ss_drisee_score_raw'] = ss_dict["drisse_score_raw"] if ss_dict.has_key("drisse_score_raw") else ""
                        metagenome_object['ss_standard_deviation_gc_ratio_preprocessed'] = ss_dict["standard_deviation_gc_ratio_preprocessed"] if ss_dict.has_key("standard_deviation_gc_ratio_preprocessed") else ""
                        metagenome_object['ss_sequence_count_processed_rna'] = ss_dict["sequence_count_processed_rna"] if ss_dict.has_key("sequence_count_processed_rna") else ""
                        metagenome_object['ss_length_min_preprocessed_rna'] = ss_dict["length_min_preprocessed_rna"] if ss_dict.has_key("length_min_preprocessed_rna") else ""
                        metagenome_object['ss_sequence_count_preprocessed'] = ss_dict["sequence_count_preprocessed"] if ss_dict.has_key("sequence_count_preprocessed") else ""
                        metagenome_object['ss_read_count_processed_rna'] = ss_dict["read_count_processed_rna"] if ss_dict.has_key("read_count_processed_rna") else ""
                        metagenome_object['ss_average_length_preprocessed'] = ss_dict["average_length_preprocessed"] if ss_dict.has_key("average_length_preprocessed") else ""
                        metagenome_object['ss_average_gc_ratio_preprocessed'] = ss_dict["average_gc_ratio_preprocessed"] if ss_dict.has_key("average_gc_ratio_preprocessed") else ""
                        metagenome_object['ss_average_ambig_chars_preprocessed'] = ss_dict["average_ambig_chars_preprocessed"] if ss_dict.has_key("average_ambig_chars_preprocessed") else ""
                        metagenome_object['ss_average_length_raw'] = ss_dict["average_length_raw"] if ss_dict.has_key("average_length_raw") else ""
                        metagenome_object['ss_ambig_sequence_count_preprocessed_rna'] = ss_dict["ambig_sequence_count_preprocessed_rna"] if ss_dict.has_key("ambig_sequence_count_preprocessed_rna") else ""
                        metagenome_object['ss_average_gc_ratio_preprocessed_rna'] = ss_dict["average_gc_ratio_preprocessed_rna"] if ss_dict.has_key("average_gc_ratio_preprocessed_rna") else ""
                        metagenome_object['ss_cluster_count_processed_aa'] = ss_dict["cluster_count_processed_aa"] if ss_dict.has_key("cluster_count_processed_aa") else ""
                        metagenome_object['ss_length_max_preprocessed_rna'] = ss_dict["length_max_preprocessed_rna"] if ss_dict.has_key("length_max_preprocessed_rna") else ""
                        metagenome_object['ss_ambig_char_count_raw'] = ss_dict["ambig_char_count_raw"] if ss_dict.has_key("ambig_char_count_raw") else ""
                        metagenome_object['ss_average_length_preprocessed_rna'] = ss_dict["average_length_preprocessed_rna"] if ss_dict.has_key("average_length_preprocessed_rna") else ""
                        metagenome_object['ss_standard_deviation_length_raw'] = ss_dict["standard_deviation_length_raw"] if ss_dict.has_key("standard_deviation_length_raw") else ""
                        metagenome_object['ss_average_gc_content_preprocessed'] = ss_dict["average_gc_content_preprocessed"] if ss_dict.has_key("average_gc_content_preprocessed") else ""
                        metagenome_object['ss_sequence_count_sims_rna'] = ss_dict["sequence_count_sims_rna"] if ss_dict.has_key("sequence_count_sims_rna") else ""
                        metagenome_object['ss_sequence_count_dereplication_removed'] = ss_dict["sequence_count_dereplication_removed"] if ss_dict.has_key("sequence_count_dereplication_removed") else ""
                        metagenome_object['ss_read_count_processed_aa'] = ss_dict["read_count_processed_aa"] if ss_dict.has_key("read_count_processed_aa") else ""
                        metagenome_object['ss_bp_count_preprocessed'] = ss_dict["bp_count_preprocessed"] if ss_dict.has_key("bp_count_preprocessed") else ""
                        metagenome_object['ss_standard_deviation_gc_content_raw'] = ss_dict["standard_deviation_gc_content_raw"] if ss_dict.has_key("standard_deviation_gc_content_raw") else ""
                        metagenome_object['ss_bp_count_raw'] = ss_dict["bp_count_raw"] if ss_dict.has_key("bp_count_raw") else ""
                        metagenome_object['ss_standard_deviation_gc_ratio_preprocessed_rna'] = ss_dict["standard_deviation_gc_ratio_preprocessed_rna"] if ss_dict.has_key("standard_deviation_gc_ratio_preprocessed_rna") else ""
                        metagenome_object['ss_average_ambig_chars_preprocessed_rna'] = ss_dict["average_ambig_chars_preprocessed_rna"] if ss_dict.has_key("average_ambig_chars_preprocessed_rna") else ""
                        metagenome_object['ss_cluster_count_processed_rna'] = ss_dict["cluster_count_processed_rna"] if ss_dict.has_key("cluster_count_processed_rna") else ""
                        metagenome_object['ss_standard_deviation_length_preprocessed_rna'] = ss_dict["standard_deviation_length_preprocessed_rna"] if ss_dict.has_key("standard_deviation_length_preprocessed_rna") else ""
                        metagenome_object['ss_clustered_sequence_count_processed_rna'] = ss_dict["clustered_sequence_count_processed_rna"] if ss_dict.has_key("clustered_sequence_count_processed_rna") else ""
                        metagenome_object['ss_ratio_reads_aa'] = ss_dict["ratio_reads_aa"] if ss_dict.has_key("ratio_reads_aa") else ""
                        metagenome_object['ss_sequence_count_preprocessed_rna'] = ss_dict["sequence_count_preprocessed_rna"] if ss_dict.has_key("sequence_count_preprocessed_rna") else ""
                        metagenome_object['ss_sequence_count_ontology'] = ss_dict["sequence_count_ontology"] if ss_dict.has_key("sequence_count_ontology") else ""
                        metagenome_object['ss_sequence_count_raw'] = ss_dict["sequence_count_raw"] if ss_dict.has_key("sequence_count_raw") else ""
                        metagenome_object['ss_clustered_sequence_count_processed_aa'] = ss_dict["clustered_sequence_count_processed_aa"] if ss_dict.has_key("clustered_sequence_count_processed_aa") else ""
                        metagenome_object['ss_average_gc_ratio_raw'] = ss_dict["average_gc_ratio_raw"] if ss_dict.has_key("average_gc_ratio_raw") else ""
                        metagenome_object['ss_average_gc_content_raw'] = ss_dict["average_gc_content_raw"] if ss_dict.has_key("average_gc_content_raw") else ""
                        metagenome_object['ss_standard_deviation_gc_content_preprocessed_rna'] = ss_dict["standard_deviation_gc_content_preprocessed_rna"] if ss_dict.has_key("standard_deviation_gc_content_preprocessed_rna") else ""
                        metagenome_object['ss_sequence_count_sims_aa'] = ss_dict["sequence_count_sims_aa"] if ss_dict.has_key("sequence_count_sims_aa") else ""
                        metagenome_object['ss_ambig_char_count_preprocessed_rna'] = ss_dict["ambig_char_count_preprocessed_rna"] if ss_dict.has_key("ambig_char_count_preprocessed_rna") else ""
                        metagenome_object['ss_bp_count_preprocessed_rna'] = ss_dict["bp_count_preprocessed_rna"] if ss_dict.has_key("bp_count_preprocessed_rna") else ""
                        metagenome_object['ss_standard_deviation_length_preprocessed'] = ss_dict["standard_deviation_length_preprocessed"] if ss_dict.has_key("standard_deviation_length_preprocessed") else ""
                        metagenome_object['ss_standard_deviation_gc_content_preprocessed'] = ss_dict["standard_deviation_gc_content_preprocessed"] if ss_dict.has_key("standard_deviation_gc_content_preprocessed") else ""
                        metagenome_object['ss_average_gc_content_preprocessed_rna'] = ss_dict["average_gc_content_preprocessed_rna"] if ss_dict.has_key("average_gc_content_preprocessed_rna") else ""
                        metagenome_object['ss_ambig_char_count_preprocessed'] = ss_dict["ambig_char_count_preprocessed"] if ss_dict.has_key("ambig_char_count_preprocessed") else ""
                        metagenome_object['ss_ambig_sequence_count_preprocessed'] = ss_dict["ambig_sequence_count_preprocessed"] if ss_dict.has_key("ambig_sequence_count_preprocessed") else ""

                    #PIPELINE PORTION
                    if metagenome['data'].has_key('pipeline_version'):
                        metagenome_object["pipeline"] = metagenome['data']['pipeline_version']
                    else:    
                        metagenome_object["pipeline"] = ""

                    if metagenome['data'].has_key('pipeline_parameters'):
                        p_dict = metagenome['data']['pipeline_parameters'] 
                        metagenome_object['pipeline_assembled'] = p_dict["assembled"] if p_dict.has_key("assembled") else "" 
                        metagenome_object['pipeline_rna_pid'] = p_dict["rna_pid"] if p_dict.has_key("rna_pid") else "" 
                        metagenome_object['pipeline_fgs_type'] = p_dict["fgs_type"] if p_dict.has_key("fgs_type") else "" 
                        metagenome_object['pipeline_filter_ambig'] = p_dict["filter_ambig"] if p_dict.has_key("filter_ambig") else "" 
                        metagenome_object['pipeline_prefix_length'] = p_dict["prefix_length"] if p_dict.has_key("prefix_length") else "" 
                        metagenome_object['pipeline_aa_pid'] = p_dict["aa_pid"] if p_dict.has_key("aa_pid") else "" 
                        metagenome_object['pipeline_publish_priority'] = p_dict["publish_priority"] if p_dict.has_key("publish_priority") else "" 
                        metagenome_object['pipeline_m5nr_sims_version'] = p_dict["m5nr_sims_version"] if p_dict.has_key("m5nr_sims_version") else "" 
                        metagenome_object['pipeline_m5nr_annotation_version'] = p_dict["m5nr_annotation_version"] if p_dict.has_key("m5nr_annotation_version") else "" 
                        metagenome_object['pipeline_filter_ln'] = p_dict["filter_ln"] if p_dict.has_key("filter_ln") else "" 
                        metagenome_object['pipeline_m5rna_annotation_version'] = p_dict["m5rna_annotation_version"] if p_dict.has_key("m5rna_annotation_version") else "" 
                        metagenome_object['pipeline_file_type'] = p_dict["file_type"] if p_dict.has_key("file_type") else "" 
                        metagenome_object['pipeline_m5rna_sims_version'] = p_dict["m5rna_sims_version"] if p_dict.has_key("m5rna_sims_version") else "" 
                        metagenome_object['pipeline_max_ambig'] = p_dict["max_ambig"] if p_dict.has_key("max_ambig") else "" 
                        metagenome_object['pipeline_bowtie'] = p_dict["bowtie"] if p_dict.has_key("bowtie") else "" 
                        metagenome_object['pipeline_filter_ln_mult'] = p_dict["filter_ln_mult"] if p_dict.has_key("filter_ln_mult") else "" 
                        metagenome_object['pipeline_dereplicate'] = p_dict["dereplicate"] if p_dict.has_key("dereplicate") else "" 
                        metagenome_object['pipeline_screen_indexes'] = p_dict["screen_indexes"] if p_dict.has_key("screen_indexes") else "" 
            

                    counter = counter + 1
#                    sys.stdout.write("Counter: " + str(counter)  + " \r" ) 
                    sys.stdout.write("Counter Time : " + str(counter) + " : Metagenome " + metagenome_object["metagenome_id"] + " : " + str(datetime.datetime.now()) + "\n") 
                    sys.stdout.flush() 
 
                    outBuffer = StringIO.StringIO() 
                    try: 
                        solr_strings = [ unicode(str(metagenome_model_object[x])) for x in solr_keys ] 
                        solr_line = "\t".join(solr_strings) 
                        outBuffer.write(solr_line + "\n") 
#                        print outBuffer.getvalue()
                    except Exception, e: 
#Warning Log
                        print str(e) 
                        print "Failed trying to write to string buffer for model " + metagenome_object['metagenome_id'] 
                    outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"','')) 
                    outBuffer.close() 
            #END METAGENOME WS OBJECT

            #NOW DO TAX_PROFILES
            tax_profile_object_count = 1
            skipNum = 0 
            limitNum = 5000 
            while tax_profile_object_count != 0:
                tax_profile_list = ws_client.list_objects({"ids": [workspace_id],"type":"Communities.TaxonomicProfile","limit":limitNum,"skip":skipNum})
                tax_profile_object_count=len(tax_profile_list)
                skipNum += limitNum 
                tax_profile_objects_list.extend(tax_profile_list) 
 
            tax_profile_objects_list.sort() 
 
            if len(tax_profile_objects_list) > 0:
                counter = 0 
                for x in tax_profile_objects_list: 
#Info log   
#                print "\t\tChecking %s, done with %s of all objects in %s" % (x[1], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name) 
                    if "TaxonomicProfile" in x[2]: 
                        done = False 
                        while not done: 
                            try: 
                                tax_profile = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}]) 
                                done = True 
                            except Exception, e: 
#Error Log  
                                print str(e) 
                                print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id) 
                        tax_profile = tax_profile[0] 

                        tax_profile_results_list = get_profile_grouping_info(tax_profile,"taxonomy")
                        level_name_dict = tax_profile_list[2]
                        total_abundance = tax_profile_list[1]
                        tax_metagenome_ref = tax_profile_list[0]
                        
                        temp_metagenome_id = ""
                        temp_metagenome_name = ""
                        if  metagenome_id_name_dict.has_key(tax_metagenome_ref):
                            temp_metagenome_id =  metagenome_id_name_dict[tax_metagenome_ref][0]
                            temp_metagenome_name = metagenome_id_name_dict[tax_metagenome_ref][1]
                        else:
                            print "WARNING NO METAGENOME FOUND FOR TaxonomicProfile : " +  tax_profile['info'][1]
                            continue

                        #go through the results and populate the rows.
                        for tax_level in level_name_dict.keys() :
                            for tax_name in level_name_dict[tax_level].keys() :
                                tax_profile_object = dict() 
                                for x in solr_keys:
                                    tax_profile_object[x] = "" 

                                tax_profile_object['object_id'] = 'kb|ws.' + str(tax_profile['info'][6]) + '.obj.' + str(tax_profile['info'][0])
                                tax_profile_object['object_workspace'] = tax_profile['info'][7] 
                                tax_profile_object['object_type'] = tax_profile['info'][2] 
                                tax_profile_object['object_name'] = tax_profile['info'][1]                             

                                tax_profile_object['tax_leaf'] = level_name_dict[tax_level][tax_name]["is_leaf"]
                                tax_profile_object['tax_level'] = tax_level
                                tax_profile_object['tax_level_description'] = tax_name
                                tax_profile_object['tax_abundance'] = round((100. * level_name_dict[tax_level][tax_name]["abundance"]/total_abundance),3) 
                                tax_profile_object['tax_evalue'] = level_name_dict[tax_level][tax_name]["e_value"]
                                tax_profile_object['tax_percent_id'] = level_name_dict[tax_level][tax_name]["percent_identity"]
                                tax_profile_object['tax_alignment_length'] = level_name_dict[tax_level][tax_name]["alignment"]
                                tax_profile_object['tax_lineage'] = level_name_dict[tax_level][tax_name]["lineage"]
                                tax_profile_object['metagenome_id'] = temp_metagenome_id
                                tax_profile_object['metagenome_name'] = temp_metagenome_name

                                outBuffer = StringIO.StringIO() 
                                try: 
                                    solr_strings = [ unicode(str(tax_profile_object[x])) for x in solr_keys ] 
                                    solr_line = "\t".join(solr_strings) 
                                    outBuffer.write(solr_line + "\n") 
                    #                        print outBuffer.getvalue()
                                except Exception, e: 
#Warning Log
                                    print str(e) 
                                    print "Failed trying to write to string buffer the taxonomic_profile_info " + tax_profile_object['metagenome_id'] 
                                outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"','')) 
                                outBuffer.close()                                
                        counter = counter + 1 
                        sys.stdout.write("Counter Time : "+ str(counter)+ " : TaxonomicProfile " + tax_profile_object["object_name"] + " : " + str(datetime.datetime.now()) + "\n") 
                        sys.stdout.flush() 

            #NOW DO FUNCTIONAL_PROFILES 
            functional_profile_object_count = 1
            skipNum = 0 
            limitNum = 5000 
            while functional_profile_object_count != 0:
                functional_profile_list = ws_client.list_objects({"ids": [workspace_id],"type":"Communities.FunctionalProfile","limit":limitNum,"skip":skipNum})
                functional_profile_object_count=len(functional_profile_list)
                skipNum += limitNum
                functional_profile_objects_list.extend(functional_profile_list)
 
            functional_profile_objects_list.sort() 
 
            if len(functional_profile_objects_list) > 0:
                counter = 0
                for x in functional_profile_objects_list:
#Info log 
                     # print "\t\tChecking %s, done with %s of all objects in %s" % (x[1], str(100.0 * float(object_counter)/len(objects_list)) + " %", workspace_name)
                    if "FunctionalProfile" in x[2]: 
                        done = False
                        while not done: 
                            try: 
                                functional_profile = ws_client.get_objects([{"wsid": str(workspace_id), "objid": x[0]}])
                                done = True
                            except Exception, e:
#Error Log 
                                print str(e)
                                print "Having trouble getting " + str(x[0]) + " from workspace " + str(workspace_id)
                        functional_profile = functional_profile[0]
 
                        functional_profile_results_list = get_profile_grouping_info(funtional_profile,"ontology")
                        level_name_dict = functional_profile_list[2]
                        total_abundance = functional_profile_list[1]
                        func_metagenome_ref = functional_profile_list[0] 
 
                        temp_metagenome_id = ""
                        temp_metagenome_name = ""
                        if  metagenome_id_name_dict.has_key(func_metagenome_ref): 
                            temp_metagenome_id =  metagenome_id_name_dict[func_metagenome_ref][0] 
                            temp_metagenome_name = metagenome_id_name_dict[func_metagenome_ref][1]
                        else:
                            print "WARNING NO METAGENOME FOUND FOR FunctionalProfile : " +  functional_profile['info'][1]
                            continue
 
                        #go through the results and populate the rows.
                        for functional_level in level_name_dict.keys() :
                            for functional_name in level_name_dict[functional_level].keys() :
                                functional_profile_object = dict()
                                for x in solr_keys:
                                    functional_profile_object[x] = ""

                                functional_profile_object['object_id'] = 'kb|ws.' + str(functional_profile['info'][6]) + '.obj.' + str(functional_profile['info'][0])
                                functional_profile_object['object_workspace'] = functional_profile['info'][7]
                                functional_profile_object['object_type'] = functional_profile['info'][2]
                                functional_profile_object['object_name'] = functional_profile['info'][1]
 
                                functional_profile_object['func_leaf'] = level_name_dict[functional_level][functional_name]["is_leaf"]
                                functional_profile_object['func_level'] = functional_level
                                functional_profile_object['func_level_description'] = functional_name
                                functional_profile_object['func_abundance'] = round((100. * level_name_dict[functional_level][functional_name]["abundance"]/total_abundance),3)
                                functional_profile_object['func_evalue'] = level_name_dict[functional_level][functional_name]["e_value"]
                                functional_profile_object['func_percent_id'] = level_name_dict[functional_level][functional_name]["percent_identity"]
                                functional_profile_object['func_alignment_length'] = level_name_dict[tax_level][tax_name]["alignment"]
                                functional_profile_object['func_lineage'] = level_name_dict[tax_level][tax_name]["lineage"]
                                functional_profile_object['metagenome_id'] = temp_metagenome_id 
                                functional_profile_object['metagenome_name'] = temp_metagenome_name
 
                                outBuffer = StringIO.StringIO() 
                                try: 
                                    solr_strings = [ unicode(str(functional_profile_object[x])) for x in solr_keys ] 
                                    solr_line = "\t".join(solr_strings) 
                                    outBuffer.write(solr_line + "\n") 
                #                        print outBuffer.getvalue()                                
                                except Exception, e: 
#Warning Log
                                    print str(e) 
                                    print "Failed trying to write to string buffer the functional_profile_info " + functional_profile_object['metagenome_id'] 
                                outFile.write(outBuffer.getvalue().encode('utf8').replace('\'','').replace('"','')) 
                                outBuffer.close() 
                        counter = counter + 1 
                        sys.stdout.write("Counter Time : "+ str(counter)+ " : TaxonomicProfile " + tax_profile_object["object_name"] + " : " + str(datetime.datetime.now()) + "\n") 
                        sys.stdout.flush() 
    outFile.close() 
                            
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create import files from workspace objects')
    parser.add_argument('--count', action="store", dest="maxNumObjects", type=int)
    parser.add_argument('--wsname', nargs=1, help='workspace name to use', required=True)
    parser.add_argument('metagenomes', action="store", nargs='*') 
    args = parser.parse_args() 
    maxNumObjects = sys.maxint 
    if args.maxNumObjects: 
        maxNumObjects = args.maxNumObjects 
 
    wsname = args.wsname[0] 
#Info Log                                                                                                                                                  
    print args.metagenomes 
    sys.stdout.write("START TIME : " + str(datetime.datetime.now())+ "\n")
    export_communities_from_ws(maxNumObjects,args.metagenomes,wsname) 
    sys.stdout.write("END TIME : " + str(datetime.datetime.now())+ "\n")


