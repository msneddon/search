#!/usr/bin/env python

"""Installation script for KBase Search."""
if __name__ == "__main__":
    import argparse
    import os
    import os.path
    import sys
    import shutil
    
    # command-line options?
    parser = argparse.ArgumentParser(description='Install parts of KBase Search.")
    parser.add_argument('--install-tomcat-config', help='copy tomcat config file for solr')
    parser.add_argument('--install-solr-config', help='copy solr files to the service deployment area')
    args = parser.parse_args() 
    
    # check for KBase environment variables, if not present use defaults
    
    # copy tomcat config files
    
    # create solr directory in deployment area, copy solr config file, copy solr core directories, copy solr war file
    
    # 