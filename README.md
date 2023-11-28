
# Ethereum Tracker

Asynchronous bot for analyzing the futures market according to the algorithm of taking into account percentage deviations from the main trading indicators with the possibility of alerting.

The algorithm works on the principle of average deviation from SMA and RSI, PSAR indices. 

## Technologies
```Python``` ```Aiohttp``` ```Aiogram``` ```Tortoise``` ```PostgreSQL``` ```Docker```


## Installation
Clone the repository to the local machine
```shell
git clone https://github.com/temirovazat/ethereum-tracker.git
```

Go to the repository directory
```shell
cd ethereum-tracker
```

Create and activate a virtual environment
```shell
python -m venv env
source env/bin/activate
```

Set project dependencies
```shell
pip install -r requirements.txt
```

Configure the configuration file .env
```shell
nano .env
```

Run the main application in the background
```shell
python -m app.main
```

Also you can build a docker app and run the container
```shell
docker-compose up -d --build
```
