

IMG_NAME = kbase/search
CONTAINER_NAME = mykbsearch

build:
	docker build . -t $(IMG_NAME)

run-bash:
	docker run -it -v $(PWD)/config:/kb/module/search/config $(IMG_NAME) bash

start-service:
	docker run -p 7078:7078 -v $(PWD)/config:/kb/module/search/config --name $(CONTAINER_NAME) $(IMG_NAME)

start-service-bg:
	docker run -p 7078:7078 -v $(PWD)/config:/kb/module/search/config --name $(CONTAINER_NAME) -d $(IMG_NAME)

rm-container:
	- docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)