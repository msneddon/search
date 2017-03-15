import flask
import os
import os.path
import logging
import ConfigParser
import time
from flask_cors import CORS

# local modules
import exceptions
import search.exceptions
import search.controllers

VERSION = '2.0.0'

# create the flask object for handling all requests
search_wsgi = flask.Flask(__name__)
CORS(search_wsgi)

@search_wsgi.route('/', methods = ['GET'])
def index():
    response = flask.jsonify({'message': "KBase Search Service v" + str(VERSION)})
    response.status_code = 200
    return response


@search_wsgi.route('/getResults', methods=['GET'])
def get_results():
    result = search.controllers.get_results(flask.request, serviceConfig)

    if type(result) != type(flask.Response):
        response = flask.make_response(result)
        response.content_type = "application/json"
        response.status_code = 200

        # search_wsgi.logger.info(response.headers)

        return response
    else:
        return result


@search_wsgi.route('/categories', methods=['GET'])
def get_categories():
    response = flask.jsonify(serviceConfig["categories"])
    response.status_code = 200
    return response


@search_wsgi.errorhandler(search.exceptions.InvalidSearchRequestError)
def invalid_request(error=None):
    search_wsgi.logger.error(error.message)
    response = flask.jsonify({'error': error.message})
    response.content_type = "application/json"
    response.status_code = 400
    return response


@search_wsgi.errorhandler(Exception)
def invalid_request(error=None):
    search_wsgi.logger.exception(error)
    response = flask.jsonify({'error': str(error)})
    response.content_type = "application/json"
    response.status_code = 500
    return response


def initLogger():
    import logging.handlers

    formatter = logging.Formatter("%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s")
    formatter.converter = time.gmtime

    if serviceConfig['search'].has_key('log_syslog') and serviceConfig['search']['log_syslog'] == 'True':
        syslog_handler = logging.handlers.SysLogHandler(facility = logging.handlers.SysLogHandler.LOG_DAEMON, 
                                                        address = "/dev/log")
        syslog_handler.setFormatter(formatter)
        search_wsgi.logger.addHandler(syslog_handler)
    
    if serviceConfig['search'].has_key('log_file'):
        file_handler = logging.FileHandler(serviceConfig['search']['log_file'])
        file_handler.setFormatter(formatter)
        search_wsgi.logger.addHandler(file_handler)
    
    configLevel = serviceConfig['search']['log_level']

    if configLevel in logging._levelNames:
        level = logging._levelNames[configLevel]
    else:
        level = logging.INFO

    search_wsgi.logger.setLevel(level)


def getLogger():
    return search_wsgi.logger


#create a categories.json file that can be loaded and sent to the client
def load_categories(config):
    categories = dict()
    try:
        categoryFile = open(os.path.join(os.path.abspath(config['search']['config_path']),'categoryInfo.json'))
        categories = flask.json.loads(categoryFile.read())
    except Exception, e:        
        search_wsgi.logger.exception(e)
        raise

    return categories


#load up all the category json plugins
def load_plugins(config):
    try:
        plugins = dict()
        pluginsDir = os.path.join(os.path.abspath(config['search']['config_path']),'plugins/categories')
        categoryPlugins = os.listdir(pluginsDir)

        for c in categoryPlugins:
            if ".json" in c:
                categoryInfoFile = open(os.path.join(pluginsDir,c))
                plugins[c.split(".json")[0]] = flask.json.loads(categoryInfoFile.read())
                categoryInfoFile.close()
    except Exception, e:
        search_wsgi.logger.exception(e)
        raise
    
    return plugins


def load_service_config():
    settings = dict()

    search_config_directory = os.environ['SEARCH_CONFIG_DIRECTORY']
    cfg_file_path = os.path.join(search_config_directory, 'search_config.ini')
    if not os.path.isfile(cfg_file_path):
        raise EnvironmentError('Search config file ('+str(cfg_file_path)+') does not exist.  Is SEARCH_CONFIG_DIRECTORY env var set?')

    config = ConfigParser.ConfigParser()
    config.read(cfg_file_path)

    for section in config.sections():
        settings[section] = dict()
        for option in config.options(section):
            settings[section][option] = config.get(section, option)
        
    settings['search']['config_path'] = search_config_directory
    settings["categories"] = load_categories(settings)
    settings["plugins"] = load_plugins(settings)
    
    for p in settings["plugins"].keys():
        settings["categories"]["categories"][p] = dict()
        settings["categories"]["categories"][p]["fields"] = settings["plugins"][p]["solr"]["visible_fields"][:]
        settings["categories"]["categories"][p]["sortable"] = settings["plugins"][p]["solr"]["sort_fields"][:]
        settings["categories"]["categories"][p]["facets"] = settings["plugins"][p]["solr"]["facet_fields"][:]
        
    #search_wsgi.logger.info(settings)    
        
    return settings


# get the service configuration settings
serviceConfig = load_service_config()
initLogger()
