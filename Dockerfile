FROM python:2.7
MAINTAINER Michael Sneddon (mwsneddon@lbl.gov)


RUN mkdir -p /kb/module/search
RUN mkdir -p /kb/module/search/
RUN chmod -R a+rw /kb/module
WORKDIR /kb/module/search

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./ .

ENTRYPOINT [ "./scripts/entrypoint.sh" ]
CMD [ ]