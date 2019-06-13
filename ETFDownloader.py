from ETF import ETF
from pymongo import MongoClient
from tqdm import tqdm  # progress bar
import csv
import json

if __name__ == "__main__":
    client = MongoClient('mongodb://root:example@localhost:27017')
    db = client.etf
    etf_collection = db.details

    with open('etflist.csv', 'r') as etflist:
        etfs = list(csv.reader(etflist))[0]

    pbar = tqdm(total=len(etfs), unit="ETF")

    for ticker in etfs:
        pbar.set_description("Processing %s" % ticker)
        if(etf_collection.find({'ticker': str(ticker)}).count() == 0):
            try:
                etf = ETF(str(ticker))
                etf_obj = etf.toDict()
                etf_id = etf_collection.insert_one(etf_obj)
            except:
                pass
        pbar.update()

    exit()
