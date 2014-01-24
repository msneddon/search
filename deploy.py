#!/usr/bin/env python

"""Installation script for KBase Search."""
if __name__ == "__main__":
    import argparse
    import os
    import os.path
    import sys
    import shutil
    
    # command-line options?
    parser = argparse.ArgumentParser(description='Install parts of KBase Search.')
    parser.add_argument('--install-tomcat-config', action='store_true', help='copy tomcat config file for solr')
    parser.add_argument('--install-solr-config', action='store_true', help='copy solr files to the service deployment area')
    args = parser.parse_args() 

    # check for KBase environment variables, if not present use defaults    

    
    # copy Tomcat config file for solr into the runtime
    if args.install_tomcat_config:    
        # copy tomcat config files
        tomcat_config_source_dir = os.path.abspath(os.path.join(os.getcwd(),"install/solr/tomcat"))
        tomcat_config_target_dir = os.path.join(os.environ["KB_RUNTIME"], "tomcat/conf")
        
        print "Installing tomcat config files to " + str(tomcat_config_target_dir)
        
        os.chdir(tomcat_config_source_dir)
        shutil.copytree(os.path.join(tomcat_config_source_dir,"Catalina"), os.path.join(tomcat_config_target_dir,"Catalina"))
    
    # copy solr cores, solr war, solr core config to deployment area
    if args.install_solr_config:
        solr_config_source_dir = os.path.abspath(os.path.join(os.getcwd(),"install/solr/config"))
        solr_config_target_dir = os.path.join(os.environ["TARGET"], "services/search/solr")

        if not os.path.exists(solr_config_target_dir):
            print "Creating directory : " + str(solr_config_target_dir)
    
            # create solr directory in deployment area
            os.makedirs(solr_config_target_dir)
        
        # copy solr core directories and core config file
        core_top_dir = os.path.join(solr_config_source_dir, "cores")
        core_files = os.listdir(core_top_dir)
        
        print core_top_dir
        print core_files
        
        for x in core_files:
            if os.path.isdir(os.path.join(core_top_dir,x)):
                print "Copying directory structure : " + os.path.join(core_top_dir, x) + " to " + os.path.join(solr_config_target_dir, x)
                shutil.copytree(os.path.join(core_top_dir, x), os.path.join(solr_config_target_dir, x))
            elif os.path.isfile(os.path.join(core_top_dir,x)):
                print "Copying file : " + os.path.join(core_top_dir, x) + " to " + solr_config_target_dir
                shutil.copy(os.path.join(core_top_dir, x), solr_config_target_dir)        
        
        # copy solr war file
        solr_runtime_source_dir = os.path.abspath(os.path.join(os.getcwd(),"install/solr/config/runtime"))
        solr_runtime_target_dir = os.path.join(os.environ["TARGET"], "services/search/solr")
        
        print "Copying solr.war file to " + solr_runtime_target_dir
        shutil.copy(os.path.join(solr_runtime_source_dir, "solr.war"), solr_runtime_target_dir)
    
    
