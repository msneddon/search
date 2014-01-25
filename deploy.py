#!/usr/bin/env python

"""Installation script for KBase Search."""
if __name__ == "__main__":
    import argparse
    import os
    import os.path
    import sys
    import shutil
    
    # command-line options
    parser = argparse.ArgumentParser(description='Install parts of KBase Search.')
    parser.add_argument('--install-tomcat-config', action='store_true', help='copy tomcat config file for solr')
    parser.add_argument('--install-solr-config', action='store_true', help='copy solr files to the service deployment area')
    parser.add_argument('--load-solr-data', nargs=2, help='load solr data; takes two arguments: a header file and a content file')
    args = parser.parse_args() 

    # check for KBase environment variables, if not present use defaults    
    if not os.environ.has_key("KB_RUNTIME"):
        os.environ["KB_RUNTIME"] = "/kb/runtime/"
    if not os.environ.has_key("TARGET"):
        os.environ["TARGET"] = "/kb/deployment/"
    
    # find out where this is running
    running_dir = os.getcwd()
    
    
    # copy Tomcat config file for solr into the runtime
    if args.install_tomcat_config:    
        # copy tomcat config files
        tomcat_config_source_dir = os.path.abspath(os.path.join(running_dir,"install/solr/tomcat"))
        tomcat_config_target_dir = os.path.join(os.environ["KB_RUNTIME"], "tomcat/conf")
        
        print "Installing tomcat config files to " + str(tomcat_config_target_dir)
        
        try:            
            os.makedirs(os.path.abspath(tomcat_config_target_dir, "Catalina/localhost"))
            shutil.copy(os.path.join(tomcat_config_source_dir, "Catalina/localhost/search.xml"), os.path.join(tomcat_config_target_dir,"Catalina/localhost/"))
        except OSError, e:
            shutil.copy(os.path.join(tomcat_config_source_dir, "Catalina/localhost/search.xml"), os.path.join(tomcat_config_target_dir,"Catalina/localhost/"))
        
        # edit the copied file and set the correct path to where the solr files are located
        search_config_file = open(os.path.join(tomcat_config_target_dir, "Catalina/localhost/search.xml"), 'r+')
        contents = search_config_file.read()
        contents = contents.replace('SOLR_PREFIX', os.path.join(os.environ["TARGET"], "services/search/solr"))
        search_config_file.seek(0)
        search_config_file.write(contents)
        search_config_file.close()
    
    # copy solr cores, solr war, solr core config to deployment area
    if args.install_solr_config:
        solr_config_source_dir = os.path.abspath(os.path.join(running_dir,"install/solr/config"))
        solr_config_target_dir = os.path.join(os.environ["TARGET"], "services/search/solr")

        if not os.path.exists(solr_config_target_dir):
            print "Creating directory : " + str(solr_config_target_dir)
    
            # create solr directory in deployment area
            os.makedirs(solr_config_target_dir)
        
        # copy solr core directories and core config file
        core_top_dir = os.path.join(solr_config_source_dir, "cores")
        core_files = os.listdir(core_top_dir)
        
        for x in core_files:
            if os.path.isdir(os.path.join(core_top_dir,x)):
                print "Copying directory structure : " + os.path.join(core_top_dir, x) + " to " + os.path.join(solr_config_target_dir, x)
                shutil.copytree(os.path.join(core_top_dir, x), os.path.join(solr_config_target_dir, x))
            elif os.path.isfile(os.path.join(core_top_dir,x)):
                print "Copying file : " + os.path.join(core_top_dir, x) + " to " + solr_config_target_dir
                shutil.copy(os.path.join(core_top_dir, x), solr_config_target_dir)        
        
        # copy solr war file
        solr_runtime_source_dir = os.path.abspath(os.path.join(running_dir,"install/solr/config/runtime"))
        solr_runtime_target_dir = os.path.join(os.environ["TARGET"], "services/search/solr")
        
        print "Copying solr.war file to " + solr_runtime_target_dir
        shutil.copy(os.path.join(solr_runtime_source_dir, "solr.war"), solr_runtime_target_dir)
    
    # load solr data from tab delimited files to tomcat
    if args.load_solr_data:
        print "Loading tab delimited files to Solr..."
        
        solr_config_source_dir = os.path.abspath(os.path.join(running_dir,"install/solr/config"))
        core_top_dir = os.path.join(solr_config_source_dir, "cores")
        
        cores = os.listdir(core_top_dir)
        cores = [x for x in cores if os.path.isdir(os.path.join(core_top_dir,x))]
        
        sys.path.append(os.path.abspath(os.path.join(running_dir,"install/bin/")))
        import loadSolrCore
        
        for x in cores:
            print "Loading data for core : " + x
            loadSolrCore.push_to_solr(args.load_solr_data[0],args.load_solr_data[1],x)
        
        
