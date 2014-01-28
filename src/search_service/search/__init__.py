import flask
import os

# create the flask object for handling all requests
search_wsgi = flask.Flask(__name__)

# load configuration information
#search_wsgi.config.from_object('')

# set up logging
import logging
import logging.handlers

syslog_handler = logging.handlers.SysLogHandler(facility=logging.handlers.SysLogHandler.LOG_DAEMON, address="/dev/log")
search_wsgi.logger.addHandler(syslog_handler)
#file_handler = logging.FileHandler(os.path.join(os.path.abspath("."), 'search.log'))
#search_wsgi.logger.addHandler(file_handler)
    
search_wsgi.logger.setLevel(logging.DEBUG)

import exceptions
import controllers
controllers.logger = search_wsgi.logger

@search_wsgi.route('/', methods = ['GET'])
def index():
    return "KBase Search Service"

@search_wsgi.route('/getResults', methods = ['GET'])
def get_results():
    try:
        return controllers.get_results(flask.request)
    except exceptions.InvalidSearchRequestError, e:
        flask.abort(400)

@search_wsgi.route('/categories', methods = ['GET'])
def get_categories():
    return controllers.get_categories()

@search_wsgi.errorhandler(404)
def not_found(error = None):
    message = { 'status': 404, 'message': 'Unable to find ' + flask.request.url }
    
    error_response = flask.jsonify(message)
    error_response.status_code = 404
    
    return error_response
