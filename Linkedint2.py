#Inspired by Linkedint

#!/usr/bin/python3

import sys
import re
import time
import requests
import subprocess
import json
import argparse
import datetime
from unidecode import unidecode
try:
    import http.cookiejar as cookielib
    from configparser import RawConfigParser
    from urllib.parse import quote_plus
except ImportError:
    import cookielib
    from ConfigParser import RawConfigParser
    from urllib import quote_plus

try: 
    input = raw_input
except NameError: 
    pass

import os
import math
import string
from bs4 import BeautifulSoup

# Setup Argument Parameters
parser = argparse.ArgumentParser(description='Discovery LinkedIn')
parser.add_argument('-u', '--keywords', help='Keywords to search')
parser.add_argument('-o', '--output', help='Output file (do not include extentions)')
args = parser.parse_args()

config = RawConfigParser()
config.read('Linkedint2.cfg')
hunter_api = config.get('Hunter', 'hunter_api')
linkedin_username = config.get('Linkedin', 'linkedin_username')
linkedin_password = config.get('Linkedin', 'linkedin_password')

# Var init
bAuto = True
bSpecific = 0
prefix = ""
suffix = ""
body = ""
csv = []

# Make a csv header for easy filtering
csv.append('"Firstname","Lastname","Email","Occupation","Location","Company ID"')

# Define the css for the html output
css = """<style>
    #employees {
        font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
        border-collapse: collapse;
        width: 100%;
    }
    #employees td, #employees th {
        border: 1px solid #ddd;
        padding: 8px;
    }
    #employees tr:nth-child(even){background-color: #f2f2f2;}
    #employees tr:hover {background-color: #ddd;}
    #employees th {
        padding-top: 12px;
        padding-bottom: 12px;
        text-align: left;
        background-color: #4CAF50;
        color: white;
    }
    </style>

    """

# Define the header for the html output
header = """<center><table id=\"employees\">
         <tr>
         <th>Photo</th>
         <th>Possible Email:</th>
         <th>Job</th>
         <th>Location</th>
         <th>Company ID</th>
         </tr>
         """
foot = "</table></center>"

def banner():
    with open('banner.txt', 'r') as f:
        data = f.read()
        print("\033[1;31m%s\033[0;0m" % data)
        print("\033[1;34mProviding you with Linkedin Intelligence")
        print("\033[1;32mAuthor: Gimpy \033[0;0m")
        print("\033[1;32mOriginal version by Vincent Yiu (@vysec, @vysecurity)\033[0;0m")
                     
# Linkedin login and return cookie
def linkedinlogin():
    URL = 'https://www.linkedin.com'
    s = requests.Session()
    rv = s.get(URL + '/uas/login?trk=guest_homepage-basic_nav-header-signin')
    p = BeautifulSoup(rv.content, "html.parser")

    csrf = p.find(attrs={'name' : 'loginCsrfParam'})['value']
    csrf_token = p.find(attrs={'name':'csrfToken'})['value']
    sid_str = p.find(attrs={'name':'sIdString'})['value']

    postdata = {'csrfToken':csrf_token,
         'loginCsrfParam':csrf,
         'sIdString':sid_str,
         'session_key':linkedin_username,
         'session_password':linkedin_password,
        }
    rv = s.post(URL + '/checkpoint/lg/login-submit', data=postdata)
    try:
        cookie = requests.utils.dict_from_cookiejar(s.cookies)
        cookie = cookie['li_at']
    except:
        print("[!] Cannot log in")
        sys.exit(0)
    return cookie

# Use linkedinlogin to get cookie ??
def authenticate():
    try:
        a = linkedinlogin()
        session = a
        if len(session) == 0:
            sys.exit("[!] Unable to login to LinkedIn.com")
        # print("[*] Obtained new session: {}\n".format(session))
        cookies = dict(li_at=session)
    except Exception as e:
        sys.exit("[!] Could not authenticate to linkedin. {}".format(e))
    return cookies

# Use Hunter.io to obtain email prefix pattern
def hunterGetPrefix():
    try:
        print("[*] Automatically using Hunter IO to determine best Prefix")
        url = "https://api.hunter.io/v2/domain-search?domain={}&api_key={}".format(suffix, hunter_api)                
        r = requests.get(url)
        content = json.loads(r.text)
        if "status" in content:
            print("[!] Rate limited by Hunter IO Key")
        
        #print content
        prefix = content['data']['pattern']
        print("[!] {}".format(prefix))
        if prefix:
            prefix = prefix.replace("{","").replace("}", "")
            if prefix == "full" or prefix == "firstlast" or prefix == "firstmlast" or prefix == "flast" or prefix == "firstl" or prefix =="first" or prefix == "first.last" or prefix == "fmlast" or prefix == "lastfirst":
                print("[+] Found {} prefix".format(prefix))
                
            else:
                print("[!] Automatic prefix search failed, please insert a manual choice")
                
        else:
            print("[!] Automatic prefix search failed, please insert a manual choice")
            
            
    except Exception as e:
        sys.exit("[!] Could not obtain prefix through Hunter.io: {}".format(e))
    return prefix
 
# Set the company ID to search for
def linkedinGetCompanyID():
    if bCompany:
        if bAuto:
            # Automatic
            # Grab from the URL 
            companyID = []
            
            #Search the company using the linkedin api
            url = "https://www.linkedin.com/voyager/api/typeahead/hits?q=blended&query={}".format(search)
            headers = {'Csrf-Token':'ajax:0397788525211216808', 'X-RestLi-Protocol-Version':'2.0.0'}
            cookies['JSESSIONID'] = 'ajax:0397788525211216808'
            r = requests.get(url, cookies=cookies, headers=headers)
            content = json.loads(r.text)
            
            for i in range(0,len(content['elements'])):
                try:
                    companyID.append(content['elements'][i]['hitInfo']['com.linkedin.voyager.typeahead.TypeaheadCompany']['id'])
                    print("[Notice] Found company ID {} for {}".format(content['elements'][i]['hitInfo']['com.linkedin.voyager.typeahead.TypeaheadCompany']['id'],content['elements'][i]['hitInfo']['com.linkedin.voyager.typeahead.TypeaheadCompany']['company']['name']))
                except:
                    continue
            if len(companyID) == 0:
                print("[WARNING] No valid company ID found in auto, please restart and find your own")
                exit()
        else:
            # Don't auto, use the specified ID
            companyID = bSpecific
        print()
    return companyID

# Get the page count for company ID result on linkedin
def linkedinGetPagesCount(companyID):
    # Fetch the initial page to get results/page counts
    if bCompany == False:
        url = "https://www.linkedin.com/voyager/api/search/cluster?count=40&guides=List()&keywords={}&origin=OTHER&q=guided&start=0".format(search)
    else:
        url = "https://www.linkedin.com/voyager/api/search/cluster?count=40&guides=List(v->PEOPLE,facetCurrentCompany->{})&origin=OTHER&q=guided&start=0".format(companyID)
        
    headers = {'Csrf-Token':'ajax:0397788525211216808', 'X-RestLi-Protocol-Version':'2.0.0'}
    cookies['JSESSIONID'] = 'ajax:0397788525211216808'
    
    r = requests.get(url, cookies=cookies, headers=headers)
    content = json.loads(r.text)
    #print(content)
    
    data_total = content['elements'][0]['total']
    
    # Calculate pages off final results at 40 results/page
    pages = int(math.ceil(data_total / 40.0))

    if pages == 0:
        pages = 1

    if data_total % 40 == 0:
        # Becuase we count 0... Subtract a page if there are no left over results on the last page
        pages = pages - 1 

    if pages == 0: 
        print("[!] No result. Try to use quotes in the search name")
        sys.exit(0)
    
    print("[*] {} Results Found".format(data_total))
    if data_total > 1000:
        pages = 25
        print("[*] LinkedIn only allows 1000 results. Refine keywords to capture all data")
    
    print()
    return pages

# Generate email from pattern
def generateEmail(data_firstname,data_lastname):
    ## a list of title to be carefull of
    titleList = ['ing','eng','caia','acca','ccp','cga','cissp','mbci','bcms','scra','crha','asa','cbv','ctp','mfin','chrp','cpa','dr','mba','msp','crisc','pcp','phd','pmp', 'crma','cfa', 'm.sc','msc', 'cpi','cipm','phd','ph.d','psm','mgp','mba','frm','ias']

    # Incase the last name is multi part, we will split it down
    parts = data_lastname.split()
    data_firstname = re.sub(r'(.*)\(.*\).*',r'\1',data_firstname)
    
    name = data_firstname + " " + data_lastname
    fname = ""
    mname = ""
    lname = ""
        
    try:
        if len(parts) == 1:
            fname = data_firstname
            mname = '?'
            lname = parts[0]
        elif len(parts) == 2:
            if any(x in parts[1].lower() for x in titleList):
                fname = data_firstname
                mname = '?'
                lname = parts[0]
            else:
                fname = data_firstname
                mname = parts[0]
                lname = parts[1]
        elif len(parts) >= 3:
            fname = data_firstname
            lname = parts[0]
        else:
            fname = data_firstname
            lname = '?'
    except:
        print("issue with name parts")
    
    try:    
        fname = re.sub('[^A-Za-z]+', '', unidecode(fname))
        mname = re.sub('[^A-Za-z]+', '', unidecode(mname))
        lname = re.sub('[^A-Za-z]+', '', unidecode(lname))
    except:
        print('issue with name regex')
    #if len(fname) == 0 or len(lname) == 0:
        # invalid user, let's move on, this person has a weird name
    #    raise Exception("Weird name - cannot find his last or first name!")
    
    # Generate user name and email base on first and last name
    user = ""
    if prefix == 'full':
        user = '{}{}{}'.format(fname, mname, lname)
    if prefix == 'firstlast':
        user = '{}{}'.format(fname, lname)
    if prefix == 'firstmlast':
        if len(mname) == 0:
            user = '{}{}{}'.format(fname, mname, lname)
        else:
            user = '{}{}{}'.format(fname, mname[0], lname)
    if prefix == 'flast':
        user = '{}{}'.format(fname[0], lname)
    if prefix == 'firstl':
        user = '{}{}'.format(fname,lname[0])
    if prefix == 'first.last':
        user = '{}.{}'.format(fname, lname)
    if prefix == 'fmlast':
        if len(mname) == 0:
            user = '{}{}{}'.format(fname[0], mname, lname)
        else:
            user = '{}{}{}'.format(fname[0], mname[0], lname)
    if prefix == 'lastfirst':
        user = '{}{}'.format(lname, fname)
    email = '{}@{}'.format(user, suffix)
    
    return email

# Search linkedin for user   
def linkedinGetSearchPeople(companyID, page):
    
    global body, csv
    
    if bCompany == False:
        url = "https://www.linkedin.com/voyager/api/search/cluster?count=40&guides=List()&keywords={}&origin=OTHER&q=guided&start={}".format(search, page*40)
    else:
        url = "https://www.linkedin.com/voyager/api/search/cluster?count=40&guides=List(v->PEOPLE,facetCurrentCompany->{})&origin=OTHER&q=guided&start={}".format(companyID, page*40)
    
    headers = {'Csrf-Token':'ajax:0397788525211216808', 'X-RestLi-Protocol-Version':'2.0.0'}
    cookies['JSESSIONID'] = 'ajax:0397788525211216808'
    
    r = requests.get(url, cookies=cookies, headers=headers)
    content = r.text.encode('utf-8')
    content = json.loads(content)

    print("[*] Fetching page {} with {} results".format((page),len(content['elements'][0]['elements'])))

    for c in content['elements'][0]['elements']:
        
        if 'com.linkedin.voyager.search.SearchProfile' in c['hitInfo'] and c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['headless'] == False:
            
            # Get data from the voyager API - First name, Lastname , Industry, occupation, location, slug
            try:
                data_industry = c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['industry']
            except:
                data_industry = ""
                
            data_firstname = c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['firstName']
            data_lastname = c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['lastName']
            data_slug = "https://www.linkedin.com/in/{}".format(c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['publicIdentifier'])
            data_occupation = c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['occupation']
            data_location = c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['location']
            
            print('[+] Found {} {}'.format(data_firstname,data_lastname))
            
            # Get Picture from voyager api
            try:
                data_picture = "{}{}".format(c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['picture']['com.linkedin.common.VectorImage']['rootUrl'],c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['picture']['com.linkedin.common.VectorImage']['artifacts'][2]['fileIdentifyingUrlPathSegment'])
            except:
                print("[*] No picture found for {} {}, {}".format(data_firstname, data_lastname, data_occupation))
                data_picture = ""
            try:
                email = generateEmail(data_firstname,data_lastname)
            except Exception as e:
                print("[!] An error occured: {}".format(e))
            
        #    try:
        #        for item in linkedinGetSearchProfile(c['hitInfo']['com.linkedin.voyager.search.SearchProfile']['miniProfile']['publicIdentifier']):
        #            job = item.split(".")
        #            if companyID in job[0]:
        #                seniority = ".".join([job[1],job[2]])
        #    except Exception as e:
        #        print(e)
        #        print("Issue was with {}".format(data_slug))
                
            # Add an HTML body for that output
            body += "<tr>" \
            "<td><a href=\"{}\"><img src=\"{}\" width=200 height=200></a></td>" \
            "<td><a href=\"{}\">{}</a></td>" \
            "<td>{}</td>" \
            "<td>{}</td>" \
            "<td>{}</td>" \
            "<a>".format(data_slug, data_picture, data_slug, email, data_occupation, data_location,companyID)

            # Add a csv entry for that outpup
            csv.append('"{}","{}","{}","{}","{}","{}"'.format(data_firstname, data_lastname, email, data_occupation, data_location,companyID.replace(",",";")))

# Search Linkedin specific user profile for more details
#Must add truttle cause we can get ban
#def linkedinGetSearchProfile(publicIdentifier):
#    
#    seniority = []
#    url = "https://www.linkedin.com/in/{}".format(publicIdentifier)
#    r = requests.get(url, cookies=cookies)
#    soup = BeautifulSoup(r.text)
#    
#    for code in soup.select('code'):
#        if 'com.linkedin.voyager.dash.identity.profile.Position' in code.contents[0]:
#            data = json.loads(code.contents[0][3:-1])
#            
#            for x in data['included']:
#                try:
#                    if x['$type'] == 'com.linkedin.voyager.dash.identity.profile.Position':
#                        if 'end' not in x['dateRange']:
#                            pjob = x['dateRange']['start']
#                            company = x['*company'][::-1].split(':')[0][::-1]
#                            seniority.append(".".join([str(company),str(pjob['year']),str(pjob['month'])]))
#
#                except Exception as e:
#                    continue
#    
#    return seniority

# Write data to files
def GenerateOutput():
    
    # Write the HTML file            
    f = open('{}.html'.format(outfile), 'w')
    f.write(css)
    f.write(header)
    f.write(body)
    f.write(foot)
    f.close()
    
    # Write the CSV
    f = open('{}.csv'.format(outfile), 'w')
    f.writelines('\n'.join(csv))
    f.close()
 

if __name__ == '__main__':

# Prompt user for data variables
    # Set search keywords
    search = args.keywords if args.keywords!=None else input("[*] Enter search Keywords (use quotes for more precise results)\n")
    print()
    # Set output file name
    outfile = args.output if args.output!=None else input("[*] Enter filename for output (exclude file extension)\n")
    print() 
    
    # Set compagny filter choices with bCompagy bool
    while True:
        bCompany = input("[*] Filter by Company? (Y/N): \n")
        if bCompany.lower() == "y" or bCompany.lower() == "n":
            if bCompany.lower() == "y":
                bCompany = True
                break
            else:
                bCompany = False
                break
        else:
            print("[!] Incorrect choice")
    print()

    # Set e-mail domain suffix
    while True:
        suffix = input("[*] Enter e-mail domain suffix (eg. contoso.com): \n")
        suffix = suffix.lower()
        if "." in suffix:
            break
        else:
            print("[!] Incorrect e-mail? There's no dot")
    print()
    
    # Set the email prefix pattern
    while True:
        prefix = input("[*] Select a prefix for e-mail generation (auto,full,firstlast,firstmlast,flast,firstl,first.last,fmlast,lastfirst): \n")
        prefix = prefix.lower()
        print()
        if prefix == "full" or prefix == "firstlast" or prefix == "firstmlast" or prefix == "flast" or prefix == "firstl" or prefix =="first" or prefix == "first.last" or prefix == "fmlast" or prefix == "lastfirst":
            break
        elif prefix == "auto":
            
            #if auto prefix then we want to use hunter IO to find it.
            try:
                prefix = hunterGetPrefix().lower()
                break
            except:
                print('\n[!] Issue with pattern from Hunter.io, Please input one manually.\n')
                continue
        else:
            print("[!] Incorrect choice, please select a value from (auto,full,firstlast,firstmlast,flast,firstl,first.last,fmlast)")
    print()
    
# Init search
    # URL Encode for the querystring
    search = quote_plus(search)
    cookies = authenticate()
    
    # Get the company ID
    companyID = linkedinGetCompanyID()
    validateCompanyID = None
    
    # If many ID is found, valide with user what to do
    if len(companyID) != 1:
        print('[!] Several company ID found\nChoose one company ID or type ALL:\n\n')
        while True:
            validateCompanyID = input("[*] Company ID or ALL?:")
            if validateCompanyID.lower() == "all" or validateCompanyID in companyID:
                if validateCompanyID.isdigit():
                    companyID = []
                    companyID.append(validateCompanyID)
                    break
                else:
                    break
            else:
                print("[!] Incorrect choice")
        print()

    # Go through IDs and do the job
    for id in companyID:
        print("[*] Using company ID: {}".format(id))
        try:
            pages = linkedinGetPagesCount(id)
            try:
                for page in range(pages):
                    linkedinGetSearchPeople(id,page)
            except Exception as e:
                print("issue getting result: {}".format(e))
                continue
        except:
            print("No result found")
            continue
            
    GenerateOutput()
    
    print("[+] Complete")
