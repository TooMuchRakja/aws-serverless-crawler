import uuid # importujemy sobie uuid do tworzenia randomowych id 
from models.visitedURLS import visitedURL # importujemy sobie zdefiniowaną klasę z parametrami tabeli dynamo db
import json 


#def oznacz_odwiedzone(tabela_ddb, visitedURL : VisitedURL):
	#tabela_ddb.put_item(Item=vars(visitedURL)) # za pomocą vars przekształcamy naszą klasę do formatu dla tabeli dynamo db 


#def wrzuc_do_kolejki(kolejka_sqs, visitedURL : VisitedURL):
	#record = json.dumps(vars(visitedURL)) # vars przekształca naszą klasę na obiekt, a json dumps przekształca z formatu python do formatu json 

	#kolejka_sqs.send_message(MessageBody = json.dumps(vars(visitedURL))) # przysłamy nasz obiekt do sqs 


def wsad_do_kolejki(kolejka_sqs, urls, runID, sourceURL, root_URL): # funkcja na cele dodawania 10 obiektów do batcha 
	obiekty = [] # do tej listy będziemy zaciągać nasze obiekty w postaci url 
	for item in urls: # iterujemy po każdym url 
		item = {
			'VisitedURL' : item, 
			'runId' : runID,
			'sourceURL' : sourceURL,
			'root_URL' : root_URL # pierwszy elemnt tutaj to klucz więc zawsze musi być spójny z tabelą Dynamo, wszystkie klucze na zielono mają być identyczne jak w tabeli !!!!
		} # tworzymy sobie słownik z obiektów po których iterujemy 
		obiekty.append(item)
	partiaObiektow = [] # tworzymy sobie pustą listę która będzie przyjmowąc partie po 10 obetków 
	rozmiarPartii = 10 # rozmiar partii 10 - tyle maksymalnie przyjmie sqs 

	for i in range(0, len(obiekty), rozmiarPartii): # iterujemy w zakresie od 0 do wszystkich wyników powyższej iteracji
		# czyli długości listy obiekty, kolejno rozmiar partii to skok o 10, czyli o maksymalny batch dla sqs (sqs może przyjąć 10 wiadmości na raz )
		partiaObiektow.append(obiekty[i:i+rozmiarPartii])
	print (f'Skonstruowana partia wynosi {len(partiaObiektow)} partii o łącznej sumie obiektów wynoszącej {len(obiekty)} ')

	# teraz stworzymy mechaniz który będzie przesyłał wszystkie partie po 10 obiektów do sqs 

	numer_partii = 0 # rozpoczynamy od numeru 0 
	for partia in partiaObiektow: # iterujemy po każdej partii 
		wejscia = [] # tworzymy pustą listę która będzie przechowywać wiadomości do przeslania 
		for item in partia: # iterujemy po obiektach w aktualnej partii, konwertujemy je na format json 
			print("\t" + json.dumps(item))
			wejscia.append({'MessageBody': json.dumps(item), 'Id':str(uuid.uuid4())}) # dodajemy wejścia w formacie json do naszej partii, a właściwie treść naszego obiektu ma być w formacie json
			# dodatkowo tworzomy unikatowe id dla każdej wiadomości, każda wiadomość musi posiadać unikalny element id, opisane poniżej 


		print(f'Przesyłanie partii numer {numer_partii} do SQS')
		kolejka_sqs.send_messages(Entries=wejscia) # tuaj używamy metody Entries, oraz messages ma być liczbą mnogą jest to specjalna metoda dla przesyłania partii w SQS, entries pozwala przesyłać 
		# kilka wiadomości na raz ( w tym wypadku 10), każda wiadomość musi być określona jako element w liście przekazanej w entries 
		# każdy element listy musi być słownikiem zawierającym pola Message Body i Id w bacthu 
		numer_partii +=1 

def partiaGetObiekt(ddbresource, urls: list[str], runId: str):
    print(f"Przekazane URL-e: {urls}")  # Debugowanie
    if not urls:
        raise ValueError("Lista URLi jest pusta. Oczekiwano co najmniej jednego elementu.")
    keys = []
    for visited_url in urls:  # Zmienna visited_url dla jasności
        keys.append({
            "VisitedURL": visited_url,  # Używamy nazwy klucza z tabeli
            "runId": runId
        })
    input = {
        'CrawlerData': { 'Keys': keys}
    }
    response = ddbresource.batch_get_item(RequestItems=input)
    items = response['Responses']['CrawlerData']
    print(f"Odpowiedź z DynamoDB: {response}")  # Debugowanie
    return items




def partiaPutObiekt(tabela_ddb, urls, runId, sourceUrl, root_URL):
    with tabela_ddb.batch_writer() as writer: # definujemy sobie menadżera kontekstu
        for item in urls:
            writer.put_item(Item={
            "VisitedURL": item,
            "runId": runId,
            "sourceURL": sourceUrl,
            "root_URL": root_URL 
        })

