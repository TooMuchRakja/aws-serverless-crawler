from datetime import datetime
from typing import List # importujemy bibliotekę typing potrzebną do typing hintow - pomocne w definiowaniu struktur danych oraz struktur wyników jakie powinny nam zwracać nasze funckje 
import uuid
import json
import logging
import boto3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from funkcje_pomocnicze.pomocnicze import *  # Zakładam, że jest potrzebne do `batchPutItems` i `batchEnqueue` - muszę jutro zdefiniować funkcję pomocnicze 

# Inicjalizacja zasobów AWS
ddb = boto3.resource('dynamodb') # definujemy klienta dynamo db
sqs = boto3.resource('sqs') # definujemy klienta 
kolejka_sqs = sqs.get_queue_by_name(QueueName='CrawlerQueue') # towrzymy zmienną dla kolejki SQS po jej nazwie 
tabela_ddb = ddb.Table('CrawlerData') # tworzymy zmienną dla tabeli Dynamo wskazująć jej nazwę 

logger = logging.getLogger() # stawiamy loggera 
logger.setLevel(logging.INFO)

def handler(event, context): # definujemy sobie handler - pamiętajmy o poprawnej nazwie, jak nie wiemymy jaka to zaglądnąć do pliku yaml template 
    print(event) # linjka do debugowania 
    eventDict = json.loads(event["Records"][0]["body"]) # ładujemy sobie event w formacie json, ale konwertujemy do pythona tak aby zrozumiał naszą składnie, json loads deserializuje dane i zamienia je na pythonowskie 
    visitedURL = eventDict["VisitedURL"]
    runId = eventDict["runId"]
    sourceURL = visitedURL
    rootURL = eventDict["root_URL"] # poprawna nazwa zmiennej to jest rootURL - należy zmienić 

    print(f"Rozpoczynanie crawla dla URL={visitedURL}, runId={runId}, sourceURL={sourceURL}, rootURL={rootURL}")

    # Step 1 - Pobieranie wszystkich linków z podanego URL
    referencje = pobierz_linki_z_URL(visitedURL) # na początku visited url będzie root URL 
    print(f"Pobrano {len(referencje)} linków z {rootURL}.")

    # Step 2 - Filtrowanie linków do konkretnej domeny
    filtruj_linki = filtruj_linki_root_URL(rootURL, referencje)  # przefiltrowane linki będziemy trzymać w zmiennej która tak naprawdę będzie listą - patrz funkcja filtruj linki root URL
    print(f"Znaleziono {len(filtruj_linki)} linków referencyjnych powiązanych z {rootURL}")

    # Step 3 - Pobieranie informacji o już odwiedzonych linkach
    odwiedzoneLinki_rekordy = pobierz_odwiedzone_adresy([visitedURL], runId)
    print(f"Odwiedzono już  {len(odwiedzoneLinki_rekordy)} link(i).")

    odwiedzoneLinki = map(lambda record: record["VisitedURL"], odwiedzoneLinki_rekordy)

    # Step 4 - Wyznaczenie linków jeszcze nieodwiedzonych
    pozostałe_cele_crawl = znajdz_nieodwiedzone(filtruj_linki,odwiedzoneLinki)
    print(f"{len(pozostałe_cele_crawl)} musi zostać jeszcze przeprocesowanych. ")
    
    if pozostałe_cele_crawl: # jeżeli są jakieś  pozostałe cele do crawlowania to ... wtedy dodajemy je do tabeli dynamo 
        # Step 5 - Oznaczanie nowych linków jako odwiedzonych
        zaznacz_odwiedzone(pozostałe_cele_crawl, runId, sourceURL, rootURL)
        print(f"Oznaczono oraz dodano do tabeli dynamo {len(pozostałe_cele_crawl)} linków.")

        # Step 6 - Dodanie nowych linków do kolejki SQS
        do_kolejki_sqs(pozostałe_cele_crawl, runId, sourceURL, rootURL)
        print(f"Wykonano wysyłkę {len(pozostałe_cele_crawl)} adresów URL do kolejki SQS.")


def do_kolejki_sqs(targets, runId, sourceUrl, root):
    wsad_do_kolejki(kolejka_sqs, targets, runId, sourceUrl, root)

def zaznacz_odwiedzone(targets, runId, sourceUrl, root):
    partiaPutObiekt(tabela_ddb, targets, runId, sourceUrl, root)

def znajdz_nieodwiedzone(potentialLinks, visitedLinks):
    nieodwiedzone = set(potentialLinks).difference(visitedLinks) # za pomocą seta tworzy róznicę pomiędzy funkcjami odwiedzonymi i nieodwiedoznoymi  która będzie zwracana w naszej funkcji
    return nieodwiedzone

def filtruj_linki_root_URL(rootURL: str, linkCandidates: List[str]): # funkcja filtrująca linki pod to aby zawierały tylko część root url i nie zawierały #, dlatego że po # zazwyczaj nie link prowadzi do nikąd 
    return [link for link in linkCandidates if rootURL in link] # w sumie tutaj przez list comprehension robimy taki oto zabieg:
    # tworzymy sobie filter w postaci tworzenia nowej listy która filtruje nam po tym że dany link zaczyna się z rootURL a potem po tym że jeżeli jakiś z linków zawiera sobie hasztag to jest rownież wywalany 
    # składnia - zmienne link możemy nazwać jak chcemy, najważniejsze jest root URL i link candiates

def pobierz_linki_z_URL(link: str) -> List[str]: # definujemy funkcję która pobierze nam wszystkie linki z naszego  
    # Inicjalizacja sesji za pomocą `requests` i pobieranie strony
    response = requests.get(link) # za pomocą tej linijki kodu request wykonuje rządzanie HTTP GET co pozwoli nam pozyskać treść storny internetowej
    if response.status_code != 200: 
        logger.warning(f"Failed to retrieve {link} with status code {response.status_code}")
        return [] # jeżeli będzie jakiś błąd to funkcja zwraca pustą listę dzięki czemu nie analizujemy stron które nie zostały popranwie pobrane 

    # Parsowanie strony HTML za pomocą BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    links = {a.get('href') for a in soup.find_all('a', href=True)}  
    pełne_linki = [urljoin(link,href) for href in links]
    print(f"Otrzymano {len(pełne_linki)} linków")
    
    return list(pełne_linki)

def pobierz_odwiedzone_adresy(candidates: List[str], runId: str) -> List[str]:
    return partiaGetObiekt(ddb, candidates, runId)








