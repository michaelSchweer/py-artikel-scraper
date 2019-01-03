import sys
import os
import urllib.request
from time import time
from time import sleep
from random import uniform
from random import shuffle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

baseUrl = '<BASE URL REDACTED>'
artikelBaseUrl = 'Article/1_1'

options = Options()
# options.add_argument('--headless')
options.add_argument('--hide-scrollbars')
options.add_argument('--disable-gpu')
options.add_argument('--log-level=3')
options.add_argument('--silent')
driver = webdriver.Chrome(options=options)
driver.get(baseUrl)
sleep(1)
os.system('cls')

def randomDelay():
    return uniform(2.3, 4.4)

def scrapeArtikel(afdelingID, artikelID):
    global sideReqs
    global gemteArtikler

    sideReqs += 1
    fuldURL = '{}/{}/{}/{}'.format(baseUrl, artikelBaseUrl, afdelingID, artikelID)
    driver.get(fuldURL)
    sleep(randomDelay())
    try:
        indhold = driver.find_element_by_class_name('wContent')
    except:
        print('[{}] 404\'er. Fortsætter med næste artikel...'.format(artikelID))
        sleep(randomDelay())
        return
    
    if indhold.text.strip().startswith('Sidst opdateret') or not indhold.text.strip():
        print('[{}] Mangler kroppen. Fortsætter med næste artikel...'.format(artikelID))
        sleep(randomDelay())
        return

    indholdTitel = indhold.get_attribute('article-title')
    indholdArtikelID = int(indhold.get_attribute('data-id'))
    indholdPortalID = int(indhold.get_attribute('p-id'))
    
    os.makedirs(str(indholdArtikelID), exist_ok=True)
    os.chdir(str(indholdArtikelID))

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
    with open(filename, 'w', encoding='utf-8') as outputFile:
        outputFile.write(indholdHTML)
    print('[{}] "{}" gemt i {}\\{}'.format(indholdArtikelID, indholdTitel, indholdArtikelID, filename))
    
    gemteArtikler += 1
    indholdPics = indhold.find_elements_by_tag_name('img')
    for pic in indholdPics:
        sleep(randomDelay())
        picUrl = pic.get_attribute('src').split('?')[0]
        picName = picUrl.split('/')[-1]
        try:
            urllib.request.urlretrieve(picUrl, picName)
            print('[{}] {} gemt i {}\\'.format(indholdArtikelID, picName, indholdArtikelID))
        except Exception as e:
            print(e)

    os.chdir('..')
    sleep(randomDelay())
    return

startTid = time()

baID = 2
sideReqs = 0
gemteArtikler = 0

# artikelID = 3116
artikler = list(range(1, 101))
shuffle(artikler)
os.chdir('output')

for artikel in artikler:
    scrapeArtikel(baID, artikel)

slutTid = time()
brugtTid = slutTid - startTid
sekPerReq = brugtTid / sideReqs
try:
    sekPerGemtArtikel = brugtTid / gemteArtikler
except ZeroDivisionError:
    sekPerGemtArtikel = 0

print('')
print('{}/{} artikler gemt på {:.2f} sekunder. {:.2f} sekunder per request, {:.2f} sekunder per gemt artikel.'.format(gemteArtikler, sideReqs, brugtTid, sekPerReq, sekPerGemtArtikel))

driver.quit()