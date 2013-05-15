all:
	setup.sh -c
	setup.sh --install-tomcat
	setup.sh --install-service
	setup.sh --install-app
	setup.sh --install-doc

install:
	setup.sh --start-tomcat
	setup.sh --import
