🕷 Serverless Web Crawler (AWS Lambda + DynamoDB + SQS)
Internetowy crawler oparty na usługach AWS, napisany w języku Python. Umożliwia analizowanie i indeksowanie stron internetowych, zaczynając od podanego adresu pierwotnego root URL, następnie rekurencyjnie odwiedza wszystkie powiązane strony wewnętrzne i wyciąga linki do tabeli DynamoDB. 

📦 Wymagania

    - AWS CLI i skonfigurowane uprawnienia
    - SAM CLI
    - Python 3.10+


📁 Struktura projektu 
.
├── crawler.py                    # Druga funkcja Lambda – analizuje i przetwarza strony
├── funkcje_pomocnicze/
│   └── pomocnicze.py            # Funkcje wspierające (np. filtrowanie, logika pomocnicza)
├── initializer.py               # Pierwsza funkcja Lambda – inicjuje crawl i uruchamia cały proces
├── models/
│   └── visitedURLS.py           # Model danych zapisywany do DynamoDB
├── requirements.txt             # Wymagane biblioteki Pythona (m.in. bs4)
├── samconfig.toml               # Konfiguracja deploymentu AWS SAM
├── template.yaml                # Szablon SAM definiujący infrastrukturę jako kod
└── .gitignore                   # Ignorowane pliki i katalogi (np. .aws-sam/)

🚀 Użyte technologie 

AWS Lambda – dwie funkcje:
    - InitializerFunction – inicjuje crawl, wrzucając linki do kolejki,
    - CrawlerFunction – przetwarza linki z kolejki i zapisuje dane.

AWS SQS – kolejka przechowująca oczekujące linki do przetworzenia.

AWS DynamoDB – baza danych przechowująca odwiedzone adresy oraz identyfikatory crawlów.

AWS SAM (Serverless Application Model) – narzędzie do definiowania infrastruktury jako kodu (IaC), będące wyższą warstwą abstrakcji nad AWS CloudFormation.

Python 3.x – język używany do implementacji funkcji Lambda.

BeautifulSoup (bs4) – biblioteka do analizy i parsowania HTML.

⚙️ Jak działa aplikacja?
🧠 Ogólny przepływ
Użytkownik (lub inne API) podaje root URL.
Funkcja Lambda nr 1 (initializer):
Generuje runID złożony z daty i unikalnego identyfikatora (UUID).
Zapisuje root URL do bazy DynamoDB jako odwiedzony (optymalizacja).
Wysyła wiadomość z root URL do kolejki SQS.
Funkcja Lambda nr 2 (crawler):
Pobiera wiadomość z kolejki SQS.
Łączy się z podaną stroną przez HTTP.
Analizuje HTML i wyciąga linki (wewnętrzne).
Filtruje tylko linki z tego samego hosta co root URL (pomija np. #, inne domeny).
Sprawdza, które linki są nowe (niewidoczne jeszcze w DynamoDB).
Nowe linki zapisuje do DynamoDB i dodaje ponownie do SQS.
Proces powtarza się rekurencyjnie, aż nie znajdzie nowych linków.

🔍 Szczegóły działania
📦 Funkcja inicjalizująca (initializer.py)
Przypisuje każdemu crawl’owi unikatowy runID oparty o datę i UUID.

UUID to unikatowy identyfikator, który pozwala uruchomić ten sam root URL wiele razy, bez błędu zapisu w bazie (UUID używany jako sort key w tabeli).

Mimo że root URL nie został jeszcze odwiedzony, zaznaczamy go jako visited, by zapobiec cyklom i duplikatom – to celowa technika optymalizacyjna.

Przesyła wiadomość do SQS z root URL.

🔁 Funkcja crawlera (crawler.py)
Działa rekurencyjnie:

🌀 Pierwsza iteracja:
Pobiera root URL z SQS (jedyny link do tej pory).

Łączy się z tą stroną, analizuje HTML.

Wyciąga wszystkie linki za pomocą BeautifulSoup lub requests-html.

Filtruje tylko linki zawierające root URL.

Odrzuca linki zawierające # (niewnoszące wartości).

Sprawdza, które linki już istnieją w DynamoDB.

Te, które są nowe, zostają:

Zapisane do DynamoDB jako odwiedzone

Dodane do kolejki SQS (do dalszego crawlowania)

🔁 Kolejne iteracje:
Każdy z nowo dodanych linków trafia ponownie do funkcji crawler.

Mechanizm rekurencyjny trwa do momentu, aż:

Wszystkie linki zostaną odwiedzone

W kolejce SQS nie będzie już nowych wiadomości

🚀 Deployment (SAM CLI)
sam build
sam deploy --guided
