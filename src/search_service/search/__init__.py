import flask
import os
import os.path
import logging
import ConfigParser

# local modules
import exceptions
import controllers

# create the flask object for handling all requests
search_wsgi = flask.Flask(__name__)


@search_wsgi.route('/', methods = ['GET'])
def index():
    response = flask.jsonify({'message': "KBase Search Service"})
    response.status_code = 200
    return response


@search_wsgi.route('/getResults', methods = ['GET'])
def get_results():
    return controllers.get_results(flask.request, serviceConfig)


@search_wsgi.route('/categories', methods = ['GET'])
def get_categories():
    return flask.jsonify(serviceConfig["categories"])


@search_wsgi.errorhandler(exceptions.InvalidSearchRequestError)
def invalid_request(error = None):
    response = flask.jsonify({'message': error.message})
    response.status_code = 400
    return response


@search_wsgi.errorhandler(Exception)
def invalid_request(error = None):
    response = flask.jsonify({'message': error.message})
    response.status_code = 500
    return response



def initialize_logging():
    import logging.handlers

    controllers.logger = search_wsgi.logger

    if serviceConfig['search'].has_key('log_syslog') and serviceConfig['search']['log_syslog'] == True:
        syslog_handler = logging.handlers.SysLogHandler(facility = logging.handlers.SysLogHandler.LOG_DAEMON, 
                                                        address = "/dev/log")
        search_wsgi.logger.addHandler(syslog_handler)
    
    if serviceConfig['search'].has_key('log_file'):
        file_handler = logging.FileHandler(serviceConfig['search']['log_file'])
        search_wsgi.logger.addHandler(file_handler)
    
    search_wsgi.logger.setLevel(logging.DEBUG)


#create a categories.json file that can be loaded and sent to the client
def load_categories(config):
    categories = dict()
    try:
        categoryFile = open(os.path.join(os.path.abspath(config['search']['config_path']),'categoryInfo.json'))
        categories = json.loads(categoryFile.read())
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
                plugins[c.split(".json")[0]] = json.loads(categoryInfoFile.read())
                categoryInfoFile.close()
    except Exception, e:
        search_wsgi.logger.exception(e)
        raise
    
    return plugins


def load_service_config():
    settings = dict()

    config = ConfigParser.ConfigParser()
    config.read("/kb/deployment/services/search/config/search_config.ini")

    for section in config.sections():
        settings[section] = dict()
        for option in config.options(section):
            settings[section][option] = config.get(section, option)
    
    categories = load_categories(settings)
    plugins = load_plugins(settings)
    
    settings["categories"] = categories
    settings["plugins"] = plugins
    
    return settings


# get the service configuration settings
serviceConfig = load_service_config()
initialize_logging()


