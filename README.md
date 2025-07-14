🧭 Note:
For best viewing of the project structure and file tree, please use the "Code" tab on GitHub.
🇵🇱 [Polska wersja](README.pl.md) dostępna tutaj.

🕷 Serverless Web Crawler (AWS Lambda + DynamoDB + SQS) 
A serverless web crawler based on AWS services, written in Python. It allows you to analyze and index websites starting from a provided root URL. It recursively visits all related internal pages and extracts links into a DynamoDB table.

📦 Requirements
    - AWS CLI with configured credentials
    - AWS SAM CLI
    - Python 3.10+

📁 Project Structure
.
├── crawler.py                    # Second Lambda function – parses and processes pages
├── funkcje_pomocnicze/
│   └── pomocnicze.py            # Supporting functions (e.g., filtering, helper logic)
├── initializer.py               # First Lambda function – initializes the crawl and triggers the process
├── models/
│   └── visitedURLS.py           # Data model saved to DynamoDB
├── requirements.txt             # Required Python libraries (e.g., bs4)
├── samconfig.toml               # AWS SAM deployment configuration
├── template.yaml                # SAM template defining infrastructure as code
└── .gitignore                   # Files and folders to be ignored (e.g., .aws-sam/)

🚀 Services Used

AWS Lambda – Two functions:
    - InitializerFunction – initiates the crawl by sending links to the queue
    - CrawlerFunction – processes links from the queue and stores data

AWS SQS – Queue for holding pending links to be crawled

AWS DynamoDB – Database storing visited URLs and crawl identifiers

AWS SAM (Serverless Application Model) – Infrastructure as Code (IaC) tool, built on top of CloudFormation

Python 3.x – Programming language used for Lambda functions

BeautifulSoup (bs4) – Library for parsing and analyzing HTML

⚙️ How the Application Works
🧠 General Flow
The user (or another API) provides a root URL.

Lambda Function #1 (initializer.py):

Generates a runID composed of the current date and a unique UUID

Saves the root URL in DynamoDB as already visited (optimization)

Sends a message containing the root URL to the SQS queue

Lambda Function #2 (crawler.py):

Receives the message from the SQS queue

Connects to the provided URL over HTTP

Parses the HTML content and extracts internal links

Filters links to keep only those from the same host as the root URL (ignores fragments like # or external domains)

Checks which links are new (not yet in DynamoDB)

New links are saved to DynamoDB and added to the SQS queue

The process repeats recursively until no new links are found.

🔍 Detailed Workflow
📦 Initializer Function (initializer.py)
Assigns each crawl a unique runID based on the date and a UUID.

The UUID allows the same root URL to be crawled multiple times without conflicts in DynamoDB (UUID is used as the sort key).

Even though the root URL hasn’t yet been crawled, it is immediately marked as visited to avoid loops and duplicates – this is an intentional optimization technique.

Sends the root URL to the SQS queue.

🔁 Crawler Function (crawler.py)
Works recursively:

🌀 First Iteration:
Receives the root URL from SQS (only one link at this point)

Connects to the page, parses the HTML

Extracts all links using BeautifulSoup or requests-html

Filters links to include only those containing the root domain

Skips links containing # (non-valuable anchors)

Checks which of the links are already stored in DynamoDB

New links are:

Stored in DynamoDB as visited

Added to the SQS queue for further crawling

🔁 Next Iterations:
Each new link is processed by the crawler function

The recursive mechanism continues until:

All reachable links have been visited

No new messages remain in the SQS queue

🚀 Deployment (SAM CLI)
sam build
sam deploy --guided