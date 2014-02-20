import xml.etree.ElementTree
import datetime
import json
import sys
import urllib2

outFile = open('publications.tab', 'w')

#outFile.write(unicode("pubmed_id\tpubmed_url\tpubdate\tjournal_title\tarticle_title\tarticle_title_sort\tauthors\tabstract\n"))

pubmed_ids = list()
month_values = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}


line = sys.stdin.readline()
while line:
#    [id, pubdate, link, title] = line.split("\t")
    [id] = line.split("\t")
    id=id.rstrip()
    pubmed_ids.append(id)
    line = sys.stdin.readline()


for x in pubmed_ids:
    done = False
    print >> sys.stderr, x

    while not done:
        try:
            data = urllib2.urlopen('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?id=' + x + '&db=pubmed&retmode=xml')
            tree = xml.etree.ElementTree.parse(data)
            root = tree.getroot()
            done = True
        except:
            pass

    doc = dict()
    doc['pubmed_id'] = x
    
    pubdate = root.findall('.//PubDate')[0]

    if type(pubdate) == str:
        doc['pubdate'] = pubdate
    else:
        medline = pubdate.find('MedlineDate')
        year = pubdate.find('Year')
        month = pubdate.find('Month')
        day = pubdate.find('Day')

        #print xml.etree.ElementTree.tostring(pubdate)

        if medline is not None:
            year = medline.text
            if year.find(' ') > -1:
                year = medline.text.split(' ')[0]
            
                if year.find('-') > -1:
                    year = int(year.split('-')[0])
                else:
                    year = int(year)

                month = medline.text
                if type(month) == str and month.find(' ') > -1:
                    month = medline.text.split(' ')[1]

                    if type(month) == str and month.find('-') > -1:
                        month = month_values[month.split('-')[0]]
                    else:
                        month = month_values[month]            
            elif year.find('-') > -1:
                year = int(year.split('-')[0])
                month = 1

            day = 1
        elif year is not None:
            year = int(pubdate.find('Year').text)

            if month is not None:
                month = pubdate.find('Month').text

                if type(month) == str:          
                    month = month_values[month]
            else:
                month = 1

            if day is not None:
                day = int(pubdate.find('Day').text)
            else:
                day = 1

        doc['pubdate'] = datetime.date(year,month,day).isoformat()
    
    doc['journal_title'] = root.findall('.//Title')[0].text
    doc['article_title'] = root.findall('.//ArticleTitle')[0].text

    try:
        doc['abstract'] = root.findall('.//AbstractText')[0].text
    except:
        doc['abstract'] = ''
    
    doc['authors'] = list()    

    author_list = root.findall('.//AuthorList/Author')    
    for author in author_list:
        lastname = author.find('LastName')
        firstname = author.find('ForeName')
        initials = author.find('Initials')
        suffix = author.find('Suffix')

        if (lastname is not None) and (firstname is not None):
            doc['authors'].append(author.find('LastName').text + "|" + author.find('ForeName').text)
        elif (lastname is not None) and (suffix is not None):
            doc['authors'].append(author.find('LastName').text + "|" + author.find('Suffix').text)
        elif (lastname is not None) and (initials is not None):
            doc['authors'].append(author.find('LastName').text + "|" + author.find('Initials').text)
        elif (initials is not None):
            doc['authors'].append(author.find('Initials').text)        

    doc['url'] = "http://www.ncbi.nlm.nih.gov/pubmed/" + x    
    outFile.write(unicode(x + '\t' + doc['url'] + '\t' + doc['pubdate'] + '\t' + doc['journal_title'] + '\t' + doc['article_title'] + '\t' + doc['article_title'].lower().replace(' ','_') + '\t' + str(doc['authors'])[1:-1].replace(',',';').replace('|',',') + '\t' + doc['abstract'] + '\n').encode('utf8'))
outFile.close()    
