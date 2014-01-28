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
    parser.add_argument('--install', action='store_true', help='install all needed tomcat and solr files')
    parser.add_argument('--install-tomcat-config', action='store_true', help='copy tomcat config file for solr')
    parser.add_argument('--install-solr-config', action='store_true', help='copy solr files to the service deployment area')
    parser.add_argument('--install-service', action='store_true', help='copy service API files to the service deployment area')
    parser.add_argument('--load-solr-data', nargs=3, help='load solr data; takes 3 arguments: the solr core to load data into, a header file, and a content file')
    args = parser.parse_args() 

    # check for KBase environment variables, if not present use defaults    
    if not os.environ.has_key("KB_RUNTIME"):
        os.environ["KB_RUNTIME"] = "/kb/runtime/"
    if not os.environ.has_key("TARGET"):
        os.environ["TARGET"] = "/kb/deployment/"
    
    # find out where this is running
    running_dir = os.getcwd()
    
    
    # copy Tomcat config file for solr into the runtime
    if args.install_tomcat_config or args.install:    
        # copy tomcat config files
        tomcat_config_source_dir = os.path.abspath(os.path.join(running_dir,"install/solr/tomcat"))
        tomcat_config_target_dir = os.path.join(os.environ["KB_RUNTIME"], "tomcat/conf")
        
        print "Installing tomcat config files to " + str(tomcat_config_target_dir)
        
        try:            
            os.makedirs(os.path.join(tomcat_config_target_dir, "Catalina/localhost"))
            shutil.copy(os.path.join(tomcat_config_source_dir, "Catalina/localhost/search.xml"), os.path.join(tomcat_config_target_dir,"Catalina/localhost/"))
            shutil.copy(os.path.join(tomcat_config_source_dir, "conf/server.xml"), tomcat_config_target_dir)
        except OSError, e:
            shutil.copy(os.path.join(tomcat_config_source_dir, "Catalina/localhost/search.xml"), os.path.join(tomcat_config_target_dir,"Catalina/localhost/"))
            shutil.copy(os.path.join(tomcat_config_source_dir, "conf/server.xml"), tomcat_config_target_dir)
        
        # edit the copied file and set the correct path to where the solr files are located
        search_config_file = open(os.path.join(tomcat_config_target_dir, "Catalina/localhost/search.xml"), 'r+')
        contents = search_config_file.read()
        contents = contents.replace('SOLR_PREFIX', os.path.join(os.environ["TARGET"], "services/search/solr"))
        search_config_file.seek(0)
        search_config_file.write(contents)
        search_config_file.close()
    
    # copy solr cores, solr war, solr core config to deployment area
    if args.install_solr_config or args.install:
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
    
    # copy service API files to deployment area
    if args.install_service or args.install:
        service_script_source_dir = os.path.abspath(os.path.join(running_dir,"install/bin"))
        service_target_dir = os.path.join(os.environ["TARGET"], "services/search")

        if not os.path.exists(service_target_dir):
            print "Creating directory : " + str(service_target_dir)
    
            # create service directory in deployment area
            os.makedirs(service_target_dir)

        startup_files = ['start_service','stop_service']
        for x in startup_files:
            if os.path.isdir(os.path.join(service_script_source_dir,x)):
                print "Copying directory structure : " + os.path.join(service_script_source_dir, x) + " to " + os.path.join(service_target_dir, x)
                shutil.copytree(os.path.join(service_script_source_dir, x), os.path.join(service_target_dir, x))
            elif os.path.isfile(os.path.join(service_script_source_dir,x)):
                print "Copying file : " + os.path.join(service_script_source_dir, x) + " to " + service_target_dir
                shutil.copy(os.path.join(service_script_source_dir, x), service_target_dir)

        virtualenv_dir = os.path.join(service_target_dir,"venv")
        
        # create a virtualenv under the services directory
        import subprocess
        subprocess.call(["virtualenv","--python","python2.7","--system-site-packages",virtualenv_dir])
        subprocess.call([os.path.join(virtualenv_dir, "bin/pip"), "install","flask","requests","httplib2"])
                
        # copy service code into the virtualenv directory
        shutil.copytree(os.path.join(running_dir,"src/search_service"), os.path.join(virtualenv_dir, "lib/python2.7/site-packages/search_service"))
        
        

    # load solr data from tab delimited files to tomcat
    if args.load_solr_data:
        sys.path.append(os.path.abspath(os.path.join(running_dir,"install/bin/")))
        import loadSolrCore
        
        print "Loading data for core : " + args.load_solr_data[0]
        loadSolrCore.push_to_solr(args.load_solr_data[1],args.load_solr_data[2],args.load_solr_data[0])
        
        
