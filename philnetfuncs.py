# This function is passed two components of a url, the general English wikipedia url
# and the reference to a particular page. It then pulls the html of the page specified
# and turns it into a parseable "soup" using the BeautifulSoup package. It verifies
# that the page has "div" components with the labels "Influenced" and "Influences" or 
# "Influenced by". These are reliable indicators of the page being a philosopher or
# at the very least an relevant figure in philosophy. If the page doesn't match an expected
# format then it returns four None. Otherwise, it calls influences_parse or influenced_by_parse
# depending on the pages format.
def parse_connections(prefix, ref):
    page = requests.get(prefix + ref)
    soup = BeautifulSoup(page.content, "lxml")

    influences = soup.find("div", string = "Influences")
    influenced = soup.find("div", string = "Influenced")
    influenced_by = soup.find("div", string = "Influenced\xa0by")

    if influences is None and influenced_by is None: return None, None, None, None
    if influenced is None: return None, None, None, None

    if influenced_by is None: return influences_parse(soup, ref)
    else: return influenced_by_parse(soup, ref)

# -----------------------------------------------------------------
# It's important to know that most philosophers had both "Influenced" and "Influences" as
# "div" components whereas most Islamic scholars had "Influenced" and "Influenced by". The
# division of the parse functions is to deal with these two cases.
# -----------------------------------------------------------------

# This function parses pages that have a "div" component called "Influences". It
# has a page's html "soup" passed as well as it's ref. It begins by finding the title
# text of the page which is the philosopher's name. It then finds the "divs" of class
# "center". The first two of which are (hopefully) reliably the "Influences" and
# "Influenced" components. Then the groups of philosophers labeled "Influences" and 
# "Influenced" are converted into list objects. 
def influences_parse(soup, ref):

    name = soup.find("h1", id = "firstHeading").text
    divs = soup.find_all("div", class_ = "center")

    infs = divs[0]
    infd = divs[1]

    infs = bs4_list_convert(infs)
    infd = bs4_list_convert(infd)

    return name, ref, infs, infd

# This function does the same as above except instead of finding "div" components 
# of class "center" it must find "ul" components of class "NavContent". This is due
# to the different html structure of pages with "div" components called "Influenced by". 
def influenced_by_parse(soup, ref):

    name = soup.find("h1", id = "firstHeading").text
    uls = soup.find_all("ul", class_ = "NavContent")

    infs = uls[0]
    infd = uls[1]

    infs = bs4_list_convert(infs)
    infd = bs4_list_convert(infd)

    return name, ref, infs, infd

# This function parses an html component containing a list of philosophers. 
# It receives a component, div, and finds all of the "a" components and extracts
# their text and ref (this may cause some issues with philosophers whose name is 
# different in their page heading than when their in a list). It then returns a list
# of all the names and refs of all of the philosophers. 
def bs4_list_convert(div):
    l = []

    for person in div.find_all("a", href = True):

        ref = person["href"]
        if ref[0:6] == "/wiki/":
            page = requests.get(prefix + ref)
            soup = BeautifulSoup(page.content, "lxml")
            name = soup.find("h1", id = "firstHeading").text
        else: name = person.text

        if not "[" in name and not "wikipedia" in ref:
            l.append([name,ref]) 

    return l

# This function is passed two string components of a url for a philosopher's wiki
# page as well as a dictionary of philosophers. If the philosophers dictionary
# is None then the function simply parses the wiki page of the one philosopher and
# returns a dictionary with just that entry. If the dictionary already has entries
# then it iterates through that philosophers influencers and influencees, parses
# their wiki page and adds them to the philosophers dictionary. It then returns the
# larger dictionary. 
def phil_crawl(prefix, ref, philosophers):

    name, ref, infs, infd = parse_connections(prefix, ref)
    if philosophers is None: return {name:[ref, [row[0] for row in infs], [row[0] for row in infd]]}

    for person in infs:
        if not person[0] in philosophers.keys():
            name, ref, ifs, ifd = parse_connections(prefix, person[1])
            if not name is None: 
                philosophers[name] = [ref, [row[0] for row in ifs], [row[0] for row in ifd]]

    for person in infd: 
        if not person[0] in philosophers.keys():
            name, ref, ifs, ifd = parse_connections(prefix, person[1])
            if not name is None: 
                philosophers[name] = [ref, [row[0] for row in ifs], [row[0] for row in ifd]]

    return philosophers

# This function is where the network is fully collected. It is passed two
# components of a philosopher's wiki page url to start the web crawl at. 
# It also takes the number of iterations which is essentially the number of
# steps away from the starting philosopher you would want to go. It starts
# by initializing the dictionary with a phil_crawl that returns a dictionary
# with just one entry. Then it iteratively goes through the entire dictionary
# and for any entry that it hasn't already, it uses phil_crawl to add all
# their connections to the dictionary. This results in a network with all the
# connections to the first philosopher that lie within the same number of
# degree as iterations
def iterated_crawl(prefix, ref, iterations):

    t0 = time.time()

    phils = phil_crawl(prefix, ref, None)
    temp = phils.copy()
    searched = []
    print(len(phils))

    for i in range(iterations):
        for key, value in phils.items():
            if not key in searched: 
                temp = phil_crawl(prefix, value[0], temp).copy()
                searched.append(key)
        phils = temp.copy()
        print(len(phils))

    print(time.time() - t0, " seconds")

    return phils

# This function uses the dateutil.parser to interpret a wide
# array of date formats and convert it into datetime objects.abs
# Since it will only interpret years with four digits I added some
# logic to add 0 to the front of years with 1, 2 or 3 digits
def date_convert(date): 

    if date is None: return None 
    elif date.isdigit() and len(date) == 4:
        return datetime.datetime.strptime(date, '%Y').date()
    elif date.isdigit() and len(date) == 3: 
        return datetime.datetime.strptime("0"+date, '%Y').date()
    elif date.isdigit() and len(date) == 2:
        return datetime.datetime.strptime("00"+date, '%Y').date()
    elif date.isdigit() and len(date) == 1:
        return datetime.datetime.strptime("000"+date, '%Y').date()
    elif re.search("[0-9]{3}-0*-0*", date): 
        return datetime.datetime.strptime("0"+date[0:3], '%Y').date()
    elif re.search("[0-9]{2}-0*-0*", date): 
        return datetime.datetime.strptime("00"+date[0:2], '%Y').date()
    elif re.search("[0-9]{1}-0*-0*", date): 
        return datetime.datetime.strptime("000"+date[0:1], '%Y').date()  
    else: return dateutil.parser.parse(date)

months = "(?:January|Jan|january|jan|February|Feb|february|feb|March|Mar|march|mar|April|Apr|april|apr|May|may|June|june|July|july|August|Aug|august|aug|September|Sept|september|sept|October|Oct|october|oct|November|Nov|november|nov|December|Dec|december|dec)"

# This function takes in a messy string that contains a date
# and pulls that date out and returns it. 
def date_clean(date):

    if date is None: return None

    # OS and O.C. dates capture
    temp1 = re.search(" OS]", date)
    temp2 = re.search("\[O.S. ", date)
    if not temp1 is None or not temp2 is None:
        day = re.search("[0-9]{1,2} " + months, date)
        year = re.search("[0-9]{3,4}", date)
        if not day is None and not year is None:
            return date_convert(day.group() + " " + year.group())


    # "^[0|00] Month [00|000|0000]"
    temp = re.search("^[0-9]{1,2} " + months + " [0-9]{2,4}[^0-9]", date)
    if not temp is None: return date_convert(temp.group()[:-1])
    
    # same as above but at anywhere in the string
    temp = re.search("[^0-9][0-9]{1,2} " + months + " [0-9]{2,4}[^0-9]", date)
    if not temp is None: return date_convert(temp.group()[1:-1])

    # same as above but it's the entire string
    temp = re.search("^[0-9]{1,2} " + months + " [0-9]{2,4}$", date)
    if not temp is None: return date_convert(temp.group())

    # same as above but it's at the end of the string
    temp = re.search("[^0-9][0-9]{1,2} " + months + " [0-9]{2,4}$", date)
    if not temp is None: return date_convert(temp.group()[1:])

    # ------------------------------------------------------------------------
    
    # "^Month [0|00], [00|000|0000]"
    temp = re.search("^" + months + " [0-9]{1,2},? [0-9]{2,4}[^0-9]",date)
    if not temp is None: return date_convert(temp.group()[:-1])
    
    # same as above but at anywhere in the string
    temp = re.search("[^A-Z]" + months + " [0-9]{1,2},? [0-9]{2,4}[^0-9]",date)
    if not temp is None: return date_convert(temp.group()[1:-1])

    # same as above but it's the entire string
    temp = re.search("^" + months + " [0-9]{1,2},? [0-9]{2,4}$",date)
    if not temp is None: return date_convert(temp.group())

    # same as above but it's at the end of the string
    temp = re.search("[^A-Z]" + months + " [0-9]{1,2},? [0-9]{2,4}$",date)
    if not temp is None: return date_convert(temp.group()[1:])

    # ------------------------------------------------------------------------
    
    # "^[00|000|0000]-00-[00|000|0000]"
    temp = re.search("^[0-9]{2,4}-[0-9]{2}-[0-9]{2,4}[^0-9]",date)
    if not temp is None: return date_convert(temp.group()[:-1])

    # same as above but at anywhere in the string
    temp = re.search("[^0-9][0-9]{2,4}-[0-9]{2}-[0-9]{2,4}[^0-9]",date)
    if not temp is None: return date_convert(temp.group()[1:-1])

    # same as above but it's the entire string
    temp = re.search("^[0-9]{2,4}-[0-9]{2}-[0-9]{2,4}$",date)
    if not temp is None: return date_convert(temp.group())

    # same as above but it's at the end of the string
    temp = re.search("[^0-9][0-9]{2,4}-[0-9]{2}-[0-9]{2,4}$",date)
    if not temp is None: return date_convert(temp.group()[1:])

    # ------------------------------------------------------------------------
    
    # "^[00|000|0000]"
    temp = re.search("^[0-9]{2,4}[^0-9]",date)
    if not temp is None: return date_convert(temp.group()[:-1])
    
    # same as above but at anywhere in the string
    temp = re.search("[^0-9][0-9]{2,4}[^0-9]",date)
    if not temp is None: return date_convert(temp.group()[1:-1])

    # same as above but it's the entire string
    temp = re.search("^[0-9]{2,4}$",date)
    if not temp is None: return date_convert(temp.group())

    # same as above but it's at the end of the string
    temp = re.search("[^0-9][0-9]{2,4}$",date)
    if not temp is None: return date_convert(temp.group()[1:])

    # ------------------------------------------------------------------------

# This function checks to make sure the table that is identified in a wiki page
# includes birth and death information. It takes in a parsed html table and 
# returns true if it doesn't include birth and death info and false if it does. 
def invalid_table(table):
    if table is None: return True

    rows = table.find_all("tr")

    for r in rows: 
        th = r.find("th")
        td = r.find("td")
        if not th is None and not td is None and th.text in ["Born","Died"] and not re.search("[0-9]{2,}", td.text) is None:
            return False

    return True

# This function takes the prefix and ref of a philosopher's
# wiki url as well as a list of variables (vars) that it scrapes
# from the wiki page's info table. It does this by first identifying
# the table ("infobox biography vcard" or "tbody") then finds the
# rows whose title matches one of the variables that were passed. 
# It then takes the full html object in the content of that row,
# wraps it into a list with the title ([title, content]) and appends
# the list to a list of these pairs and returns that.
def table_scrape(prefix, ref, vars):

    page = requests.get(prefix + ref)
    soup = BeautifulSoup(page.content, "lxml")

    table = soup.find("table", class_ = "infobox vcard")
    if invalid_table(table):
        table = soup.find("table", class_ = "infobox biography vcard")
    if invalid_table(table):
        table = soup.find("tbody")
        
    rows = table.find_all("tr")

    row_dict = {}
    for r in rows:
        th = r.find("th")
        td = r.find("td")
        if not th is None and not td is None and th.text in vars:
            if th.text in ["Born","Died"]: row_dict[th.text] = date_clean(td.text)
    
    var_list = []
    for var in vars:
        if var in row_dict:
            var_list.append([var,row_dict[var]])
        else: var_list.append([var,None])
        
    return var_list

# This function takes in the correct wiki url prefix, 
# a dictionary of philosophers as produced by
# iterated_crawl, and a list of variables to scrape.
# It iterates through the dictionary of philosophers
# and adds the variables produced by table_scrape for
# each philosopher.
def add_info(prefix, phils, vars):

    for key, value in phils.items():
        attrs = table_scrape(prefix,value[0],vars)
        for a in attrs:
            value.append(a[1])

    return phils

# This function creates a list of all the directed edges by 
# taking the union of connections. (e.g. if it's listed
# on Descartes page that he influenced Kant but it 
# doesn't list on Kant's page that he was influenced
# by Descartes it will appear as a connection). It
# takes in the network as collected by iterated_crawl
# then returns a list of pairs where the first entry
# in each pair influenced the second entry in the pair
def edge_finder(network):

    edges = []

    for key, value in network.items():

        for infs in value[1]:
            if infs in network:
                temp = [infs,key]
                if not temp in edges:
                    edges.append(temp)

        for infd in value[2]:
            if infd in network:
                temp = [key,infd]
                if not temp in edges:
                    edges.append(temp)

    return edges