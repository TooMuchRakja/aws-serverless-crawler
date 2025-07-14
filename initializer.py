from datetime import datetime # biblioteka potrzebna nam d stworzenia sobie daty 
import json # standarodowo do konwertowania treści python na format json 
import boto3 # boto3 do obsługi narzędzi AWS - w tym wypadku będą to SQS oraz DynamoDB
import uuid # do stworzenia unikatowego ID 
import logging # do tworzenia logów informujących co się dzieje w danej chwili 
from models.visitedURLS import visitedURL # tutaj z folderu models oraz po kropce . pliku visitedURLS importujemy sobie klasę visitedURL
# do wkładu do mojej tabeli DynamoDB 

logger = logging.getLogger() # składnia typowa dla loggera, będzie on potrzebny do tworzenia sobie logów informacyjnych 
logger.setLevel(logging.INFO)

runID_dzielnik = '#' # dzielnik dla przyszłego id które będziemy tworzyć dla każdego rekordu tabeli 

# tworzymy sobie klientów boto3: klienta dla dynamodb oraz dla sqs 
dynamodb = boto3.resource('dynamodb') # definujemy klienta dynamo db 
sqs = boto3.resource('sqs') # definujemy klienta sqs 

# pobieramy kolejkę sqs oraz tabelę dynamodb na podstawie ich nazw 
kolejka_sqs = sqs.get_queue_by_name(QueueName='CrawlerQueue') # nazwa kolejki wzięta ze stacka który stworzyłem za pomocą AWS SAM (Serverless Application Model)
tabela_ddb = dynamodb.Table('CrawlerData') # nazwa kolejki wzięta ze stacka który stworzyłem za pomocą AWS SAM (Serverless Application Model)

def handler(event, context): # definicja handlera funkcji 
	
	# pobieramy główny url z naszego zdarzenia które później sami zainicjujemy podając w nim odpowiednie url 
	root_URL = event['root_URL']
	
	# generujemy sobie unikatowe ID dla naszego crawla za pomocą funkcji wygeneruj ID opisanej pod spodem 
	runId = wygenerujID()
	
	# tworzymy sobie loggera który powie nam o zaincijowaniu crawla 
	logger.info(f'Crawl rozpoczęty, jego runId to {runId}, root URL to: {root_URL}')
	
	#tworzymy sobie obiekt "visitedURLS" przechowujący dane o root URL-u i runId
	OdwiedzURL = visitedURL(root_URL, runId, None, root_URL) # dwa razy root url, ponieważ jest to pierwszy odwiedzony url który na początku jest również visited url 
	# w zmiennej OdwiedzURL tak naprawnde przechowujemy sobie cztery zmienne zdefiniowane jako klasa wcześniej 

	# zapisujemy dane o odwiedzonym URL w tabeli dynamodb
	# tabela oprócz partition oraz sort key doda nam pozostałe parametry do rekordu, dane dodajemy do tabeli ze wczesniej stworzonego obiektu OdwiedzURL
	tabela_ddb.put_item(Item = {
		'VisitedURL' : OdwiedzURL.VisitedURL, # para klucz wartość url który został odwiedzony, w naszym obiekcie OdwiedzURL root_URL jest odpowiednikiem Visited_URL z klasy visited_URL
		'runId' : OdwiedzURL.runId, # dodajemy runID do tabeli 
		'sourceURL' : OdwiedzURL.sourceURL, # dodajemy sourceURL do tabeli 
		'root_URL' :  OdwiedzURL.root_URL # dodajemy root url do tabeli 
		})
	# przygotowujemy dane do wysyłki do kolejki SQS w formacie JSON 
	sqs_message = {
		'VisitedURL' : OdwiedzURL.VisitedURL,
		'runId' : OdwiedzURL.runId,
		'sourceURL' : OdwiedzURL.sourceURL,
		'root_URL' : OdwiedzURL.root_URL

	}

	# wysyłamy wiadomość do kolejki sqs, aby za chwile funckja crawlująca mogła to przejąć i przeprocesować crawl z kolejki 
	kolejka_sqs.send_message(MessageBody=json.dumps(sqs_message)) # treść wiadomości czyli body przkierowujemy do formatu json 
	logger.info(f' Przesłano wiadomośc {sqs_message} do kolejki SQS.')

#Funkcja definiująca uniklany generator runId
def wygenerujID () -> str: # -> str to hint czyli info w jakiej strukturze danych funkcja powinna być zwrócona, jednak w reszcie pozcyji funkcji sami musimy sobie zdefionuiować wartośći string 
	czas = datetime.now().strftime("%Y%m%d%H%M%S")
	unikatoweID = uuid.uuid4()

	runId = f'{czas}{runID_dzielnik}{unikatoweID}'

	return runId

