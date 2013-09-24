TOP_DIR = ../..
DEPLOY_RUNTIME ?= /kb/runtime
TARGET ?= /kb/deployment
SERVICE_SPEC = 
SERVICE_NAME = search
SERVICE_PORT = 7070

include $(TOP_DIR)/tools/Makefile.common

# to wrap scripts and deploy them to $(TARGET)/bin using tools in
# the dev_container. right now, these vars are defined in
# Makefile.common, so it's redundant here.
SERVICE_DIR = search
TOOLS_DIR = $(TOP_DIR)/tools
WRAP_PERL_TOOL = wrap_perl
WRAP_PERL_SCRIPT = bash $(TOOLS_DIR)/$(WRAP_PERL_TOOL).sh
SRC_PERL = $(wildcard scripts/*.pl)

# You can change these if you are putting your tests somewhere
# else or if you are not using the standard .t suffix
CLIENT_TESTS = $(wildcard client-tests/*.t)
SCRIPTS_TESTS = $(wildcard script-tests/*.t)
SERVER_TESTS = $(wildcard server-tests/*.t)

# This is a very client centric view of release engineering.
# We assume our primary product for the community is the client
# libraries,a command line interfaces, and the related documentation
# from which specific science applications can be built.
#
# A service is composed of a client and a server, each of which
# should be independently deployable. Clients are composed of
# an application programming interface and a command line
# interface. In our make targets, the deploy-service deploys
# the server, the deploy-client deploys the application
# programming interface libraries, and the deploy-scripts deploys
# the command line interface (usually scripts written in a
# scripting language but java executables also qualify), and the
# deploy target would be equivelant to deploying a service (client
# libs, scripts, and server).
#
# Because the deployment of the server side code depends on the
# specific software module being deployed, the strategy needs
# to be one that leaves this decision to the module developer.
# This is done by having the deploy target depend on the
# deploy-service target. The module developer who chooses for
# good reason not to deploy the server with the client simply
# manages this dependancy accordingly. One option is to have
# a deploy-service target that does nothing, the other is to
# remove the dependancy from the deploy target.
#
# A smiliar naming convention is used for tests. 


default:
	echo Default target is currently a no-op.

install:
	./setup.sh --install

# Test Section

test: test-init test-client test-scripts test-service


test-init: 
	./setup.sh --test
	

# test-all is deprecated. 
# test-all: test-client test-scripts test-service
#
# What does it mean to test a client. This is a test of a client
# library. If it is a client-server module, then it should be
# run against a running server. You can say that this also tests
# the server, and I agree. You can add a test-service dependancy
# to the test-client target if it makes sense to you. This test
# example assumes there is already a tested running server.
test-client:
	# run each test
	for t in $(CLIENT_TESTS) ; do \
		if [ -f $$t ] ; then \
			$(DEPLOY_RUNTIME)/bin/perl $$t ; \
			if [ $$? -ne 0 ] ; then \
				exit 1 ; \
			fi \
		fi \
	done

# What does it mean to test a script? A script test should test
# the command line scripts. If the script is a client in a client-
# server architecture, then there should be tests against a 
# running server. You can add a test-service dependancy to the
# test-client target. You could also add a deploy-service and
# start-server dependancy to the test-scripts target if it makes
# sense to you. Future versions of the make files for services
# will move in this direction.
test-scripts:
	@echo "running client and test-scripts"

# What does it mean to test a server. A server test should not
# rely on the client libraries or scripts in so far as you should
# not have a test-service target that depends on the test-client
# or test-scripts targets. Otherwise, a circular dependency
# graph could result.
test-service:
	@echo "running client and test-service"

# Deployment:
# 
# We are assuming our primary product to the community are
# client side application programming interface libraries and
# command line interface (scripts). The deployment of client
# artifacts should not be dependent on deployment of a server,
# although we recommend deploying the server code with the
# client code when the deploy target is executed. If you have
# good reason not to deploy the server at the same time as the
# client, just delete the dependancy on deploy-service. It is
# important to note that you must have a deploy-service target
# even if there is no server side code to deploy.
#

deploy: deploy-client deploy-service

# deploy-all deploys client *and* server is depricated and should
# be replaced by the deploy target.

deploy-all: deploy-client deploy-service

# Deploy client should deploy the client artifacts, mainly
# the application programming interface libraries, command
# line scripts, and associated reference documentation.

deploy-client: deploy-libs deploy-scripts deploy-docs
	echo "nothing to do for deploy-client"

# The deploy-libs and deploy-scripts targets are used to recognize
# and delineate the client types, mainly a set of libraries that
# implement an application programming interface and a set of 
# command line scripts that provide command based execution of
# individual api functions and aggregated sets of api functions.

deploy-libs: build-libs
	echo "nothing to do for deploy-libs"

# Deploying scripts needs some special care. They need to run
# in a certain runtime environment. Users should not have
# to modify their user environments to run kbase scripts other
# than just sourcing a single user-env script. The creation
# of this user-env script is the responsibility of the code
# that builds all the kbase modules. In the code below, we
# run a script in the dev_container tools directory that 
# wraps perl scripts. The name of the perl wrapper script is
# kept in the WRAP_PERL_SCRIPT make variable. This script
# requires some information that is passed to it by way
# of exported environment variables in the bash script below.
#
# What does it mean to wrap a perl script? To wrap a perl
# script means that a bash script is created that sets
# all required envirnment variables and then calls the perl
# script using the perl interperter in the kbase runtime.
# For this to work, both the actual script and the newly 
# created shell script have to be deployed. When a perl
# script is wrapped, it is first copied to TARGET/plbin.
# The shell script can now be created because the necessary
# environment variables are known and the location of the
# script is known. 

deploy-scripts:
	echo "nothing to do for deploy-scripts"

# Deploying a server refers to the deployment of ...{TODO}
# Deploying a service refers to the code that implements the logic
# that handles requests from remote clients. Typically, this can
# be thought of as the code that is deployed on a server (server-side code).
# This target should include the creation of a start and stop server script.
# The start server script needs to know the service port and needs
# to set the $KB_DEPLOYMENT_CONFIG environment variable.
deploy-service:
	./setup.sh --install

# Deploying docs here refers to the deployment of documentation
# of the API. We'll include a description of deploying documentation
# of command line interface scripts when we have a better understanding of
# how to standardize and automate CLI documentation.

deploy-docs: build-docs
	echo "nothing to do for for deploy-docs"

# The location of the Client.pm file depends on the --client param
# that is provided to the compile_typespec command. The
# compile_typespec command is called in the build-libs target.

build-docs: compile-docs
	echo "nothing to do for for build-docs"

# Use this if you want to unlink the generation of the docs from
# the generation of the libs. Not recommended, but could be a
# reason for it that I'm not seeing.
# The compile-docs should depend on build-libs so that we are ensured
# of having a set of documentation that is based on the latest
# type spec.

compile-docs: build-libs

# Build libs should be dependent on the type specification and the
# type compiler. Building the libs in this way means that you don't
# need to put automatically generated code in a source code version
# control repository (ie cvs, git). It also ensures that you always
# have the most  up-to-date libs and documentation if your compile
# docs depends on the compiled libs.

build-libs:
	echo "nothing to do for for build-libs"

