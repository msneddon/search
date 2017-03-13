

CONTAINER_NAME = kbsearch

build:
	docker build . -t $(CONTAINER_NAME)
