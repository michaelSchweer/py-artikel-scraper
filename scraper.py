import sys
import os
import urllib.request
import re
import base64
from datetime import datetime
from time import time
from time import sleep
from random import uniform
from random import shuffle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def cleanHTML(indholdHTML):
    indholdHTML = indholdHTML.replace('<div id="DOM_Fallback"></div>', '')

    # javascript-stripper
    patternJS = re.compile(r'<(script).*?</\1>(?s)')
    indholdHTML = re.sub(patternJS, '', indholdHTML)

    # html tags stripper
    patternITag = re.compile("(<i .*?>)")
    indholdHTML = re.sub(patternITag, '', indholdHTML)
    patternInputTag = re.compile("(<input.*?>)")
    indholdHTML = re.sub(patternInputTag, '', indholdHTML)

    # html attrs stripper
    patternClass = re.compile('( class=".*?")')
    indholdHTML = re.sub(patternClass, '', indholdHTML)
    patternId = re.compile('( id=".*?")')
    indholdHTML = re.sub(patternId, '', indholdHTML)
    patternTitle = re.compile('( title=".*?")')
    indholdHTML = re.sub(patternTitle, '', indholdHTML)
    patternStyle = re.compile('( style=".*?")')
    indholdHTML = re.sub(patternStyle, '', indholdHTML)
    patternEdit = re.compile('( contenteditable=".*?")')
    indholdHTML = re.sub(patternEdit, '', indholdHTML)

    indholdHTML = indholdHTML.replace('</i>', '')
    indholdHTML = indholdHTML.replace('\t', '')

    indholdHTML = re.sub(' +', ' ', indholdHTML)
    return indholdHTML

def logger(payload):
    print(payload)
    with open(os.path.join('logs', logFileName), 'a', encoding='utf-8') as logger:
        logger.write(str(payload) + '\n')

def randomDelay():
    return uniform(1.2, 2.4)

def getPic(picUrl, picPath):
    try:
        urllib.request.urlretrieve(picUrl, picPath)
        return True
    except Exception as e:
        logger(e)
        return False

def getBase64(srcBase64, artikelID, picNo):
    try:
        picExt = srcBase64.split('data:image/')[1].split(';base64,')[0]
        strBase64 = srcBase64.split(';base64,')[1].split('\">')[0]
        picData = base64.b64decode(strBase64)

        picName = '{}-{}-{}.{}'.format(baID, artikelID, str(picNo).zfill(3), picExt)
        picPath = os.path.join('output', str(baID), str(artikelID), picName)
        
        with open(picPath, 'wb') as f:
            f.write(picData)
    
        strPicGemt = '[{}] base64  =>  {}'.format(artikelID, picName)   
        logger(strPicGemt)
        return True

    except Exception as e:
        logger(e)
        return False

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
        str404 = '[{}] 404\'er...'.format(artikelID)
        logger(str404)
        if huuumanEmu:
            sleep(randomDelay())
        return
    
    if indhold.text.strip().startswith('Sidst opdateret') or not indhold.text.strip():
        strManglerKroppen = '[{}] Mangler kroppen...'.format(artikelID)
        logger(strManglerKroppen)
        if huuumanEmu:
            sleep(randomDelay())
        return

    indholdTitel = indhold.get_attribute('article-title')
    indholdArtikelID = int(indhold.get_attribute('data-id'))
    indholdPortalID = int(indhold.get_attribute('p-id'))
    
    os.makedirs(os.path.join('output', str(baID), str(indholdArtikelID)), exist_ok=True)
    indholdHTML = indhold.get_attribute('innerHTML').strip()
    indholdHTML = cleanHTML(indholdHTML)

    relateretIDs = []
    try:
        relateret = driver.find_element_by_class_name('rel_art')
        relateretTags = relateret.find_elements_by_tag_name('a')
        for tag in relateretTags:
            link = tag.get_attribute('href')
            relateretIDs.append(link.split('/')[-1])
    except:
        pass
    
    indholdPics = indhold.find_elements_by_tag_name('img')
    gemtePics = 0
    fejledePics = []
    for pic in indholdPics:
        if huuumanEmu:
            sleep(randomDelay())
        picUrl = pic.get_attribute('src').split('?')[0]
        if ';base64,' in picUrl:            
            gotPic = getBase64(picUrl, artikelID, gemtePics)
            if gotPic:
                gemtePics += 1
                continue
            else:
                strFejl = '[{}] Fejlede...'
                logger(strFejl)
                break
        picExt = picUrl.split('.')[-1]
        picName = '{}-{}-{}.{}'.format(indholdPortalID, indholdArtikelID, str(gemtePics).zfill(3), picExt)
        picPath = os.path.join('output', str(baID), str(indholdArtikelID), picName)
        
        picGotten = getPic(picUrl, picPath)
        
        tries = 3
        while tries:
            if picGotten:
                strPicGemt = '[{}] {}  =>  {}'.format(indholdArtikelID, picUrl, picName)
                gemtePics += 1   
                logger(strPicGemt)
                break
            else:
                tries -= 1
                strPicFejl = '[{}] {} fejlede. {} forsøg tilbage. Sover i 15 sek...'.format(indholdArtikelID, picUrl, tries)
                logger(strPicFejl)
                sleep(15)
                if not tries:
                    fejledePics.append(picUrl)
                    break
                picGotten = getPic(picUrl, picPath)
    
    if fejledePics:
        strPicFejlListe = '[{}] Der opstod fejl under hentningen af følgende billeder:'.format(artikelID)
        logger(strPicFejlListe)
        patternImgTag = re.compile("(<img.*?>)")
        alleImgTags = re.findall(patternImgTag, indholdHTML)
        for fejl in fejledePics:
            strPicFejlPic = '[{}] {}'.format(artikelID, fejl)
            logger(strPicFejlPic)
            for tag in alleImgTags:
                if fejl.replace('/', '') in tag.replace('/', ''):
                    indholdHTML = indholdHTML.replace(tag, '')
                    strPicTagSlettet = '[{}] {} slettet fra HTML'.format(artikelID, tag)
                    logger(strPicTagSlettet)

    indholdHTML = '<h2>{}</h2>{}<div id="relateret">{}</div>'.format(indholdTitel, indholdHTML, ','.join(relateretIDs))
    filename = '{}-{}.html'.format(indholdPortalID, indholdArtikelID)
    with open(os.path.join('output', str(baID), str(indholdArtikelID), filename), 'w', encoding='utf-8') as outputFile:
        outputFile.write(indholdHTML)
    strArtikelGemt = '[{}] "{}" gemt i {}\\{}\\{}'.format(indholdArtikelID, indholdTitel, baID, indholdArtikelID, filename)
    logger(strArtikelGemt)
    gemteArtikler += 1

    if huuumanEmu:
        sleep(randomDelay())
    return

os.system('cls')
baID = int(input('Afdeling?: '))
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

baseUrl = '<BASE URL>'
artikelBaseUrl = 'Article/1_1'
klokkenEr = str(datetime.now())
logFileName = '{}.log'.format(klokkenEr.replace(':', '_'))
userName = os.environ['USERNAME']
computerName = os.environ['COMPUTERNAME']
print('')
strStart = 'Startet af {} @ {}, {}'.format(userName, computerName, klokkenEr)
logger(strStart)

options = Options()
# options.add_argument('--headless') # kommentér denne linje ud for at få vist browseren under eksekvering
options.add_argument('--hide-scrollbars')
options.add_argument('--disable-gpu')
options.add_argument('--log-level=3')
options.add_argument('--silent')
driver = webdriver.Chrome(options=options)
driver.get(baseUrl)
print('')
sleep(1)
startTid = time()

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
logger(strResultat)
