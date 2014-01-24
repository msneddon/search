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

    
    if args.install_tomcat_config:    
        # copy tomcat config files
        tomcat_config_source_dir = os.path.abspath(os.path.join(os.getcwd(),"install/solr/tomcat"))
        tomcat_config_target_dir = os.path.join(os.environ["KB_RUNTIME"], "tomcat/conf")
        
        print "Installing tomcat config files to " + str(tomcat_config_target_dir)
        
        os.chdir(tomcat_config_source_dir)
        shutil.copytree(os.path.join(tomcat_config_source_dir,"Catalina"), os.path.join(tomcat_config_target_dir,"Catalina"))
    
    if args.install_solr_config:
        # create solr directory in deployment area, copy solr config file, copy solr core directories, copy solr war file
        pass
    
    
    
