import sys
import os
import urllib.request
from datetime import datetime
from time import time
from time import sleep
from random import uniform
from random import shuffle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

os.system('cls')
valg = input('\nArtikler?: ')
print('\nInfo: For at vi ikke kommer til at DoS\'e target kan vi indføre randomness og delays som ved normal browsing')
huuuman = input('Menneske-emulering (j/n)? ').lower()
huuumanEmu = False
if huuuman == 'j' or huuuman == 'ja':
    huuumanEmu = True

try:
    startArtikel = int(valg.split('-')[0])
    slutArtikel = int(valg.split('-')[1]) + 1
    artikler = list(range(startArtikel, slutArtikel))
    if huuumanEmu:
        shuffle(artikler)
except:
    print('\nLæs > Manual: X-Y')
    sys.exit()

baseUrl = '<BASEURL REDACTED>'
artikelBaseUrl = 'Article/1_1'
klokkenEr = str(datetime.now())
logFileName = '{}.log'.format(klokkenEr.replace(':', '_'))

options = Options()
# options.add_argument('--headless')
options.add_argument('--hide-scrollbars')
options.add_argument('--disable-gpu')
options.add_argument('--log-level=3')
options.add_argument('--silent')
driver = webdriver.Chrome(options=options)
driver.get(baseUrl)
print('')
sleep(1)

def logger(payload):
    with open(os.path.join('logs', logFileName), 'a', encoding='utf-8') as logger:
        logger.write(payload + '\n')

def randomDelay():
    return uniform(1.2, 2.4)

def scrapeArtikel(afdelingID, artikelID):
    global sideReqs
    global gemteArtikler

    sideReqs += 1
    fuldURL = '{}/{}/{}/{}'.format(baseUrl, artikelBaseUrl, afdelingID, artikelID)
    driver.get(fuldURL)
    if huuumanEmu:
        sleep(randomDelay())
    try:
        indhold = driver.find_element_by_class_name('wContent')
    except:
        str404 = '[{}] 404\'er. Fortsætter med næste artikel...'.format(artikelID)
        print(str404)
        logger(str404)
        if huuumanEmu:
            sleep(randomDelay())
        return
    
    if indhold.text.strip().startswith('Sidst opdateret') or not indhold.text.strip():
        strManglerKroppen = '[{}] Mangler kroppen. Fortsætter med næste artikel...'.format(artikelID)
        print(strManglerKroppen)
        logger(strManglerKroppen)
        if huuumanEmu:
            sleep(randomDelay())
        return

    indholdTitel = indhold.get_attribute('article-title')
    indholdArtikelID = int(indhold.get_attribute('data-id'))
    indholdPortalID = int(indhold.get_attribute('p-id'))
    
    os.makedirs(os.path.join('output', str(indholdArtikelID)), exist_ok=True)

    indholdHTML = indhold.get_attribute('innerHTML').strip()
    indholdHTML = indholdHTML.replace('/Content/uploaded/editor_img/', '')
    indholdHTML = indholdHTML.replace('?type=Images&amp;responseType=json', '')

    relateretIDs = []
    try:
        relateret = driver.find_element_by_class_name('rel_art')
        relateretTags = relateret.find_elements_by_tag_name('a')
        for tag in relateretTags:
            link = tag.get_attribute('href')
            relateretIDs.append(link.split('/')[-1])
    except:
        pass

    indholdHTML = '<h2>{}</h2>{}<div id="relateret">{}</div>'.format(indholdTitel, indholdHTML, ','.join(relateretIDs))

    filename = '{}-{}.html'.format(indholdPortalID, indholdArtikelID)
    with open(os.path.join('output', str(indholdArtikelID), filename), 'w', encoding='utf-8') as outputFile:
        outputFile.write(indholdHTML)
    strArtikelGemt = '[{}] "{}" gemt i {}\\{}'.format(indholdArtikelID, indholdTitel, indholdArtikelID, filename)
    print(strArtikelGemt)
    logger(strArtikelGemt)
    gemteArtikler += 1
    indholdPics = indhold.find_elements_by_tag_name('img')
    for pic in indholdPics:
        if huuumanEmu:
            sleep(randomDelay())
        picUrl = pic.get_attribute('src').split('?')[0]
        picName = picUrl.split('/')[-1]
        try:
            urllib.request.urlretrieve(picUrl, os.path.join('output', str(indholdArtikelID), picName))
            strPicGemt = '[{}] {} gemt i {}\\'.format(indholdArtikelID, picName, indholdArtikelID)
            print(strPicGemt)
            logger(strPicGemt)
        except Exception as e:
            print(e)

    if huuumanEmu:
        sleep(randomDelay())
    return

startTid = time()

baID = 2
sideReqs = 0
gemteArtikler = 0
for artikel in artikler:
    scrapeArtikel(baID, artikel)

driver.quit()
slutTid = time()
brugtTid = slutTid - startTid
sekPerReq = brugtTid / sideReqs
try:
    sekPerGemtArtikel = brugtTid / gemteArtikler
except ZeroDivisionError:
    sekPerGemtArtikel = 0

strResultat = '\n{}/{} artikler gemt på {:.2f} sekunder. {:.2f} sekunder per request, {:.2f} sekunder per gemt artikel.'.format(gemteArtikler, sideReqs, brugtTid, sekPerReq, sekPerGemtArtikel)
print(strResultat)
logger(strResultat)
