from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import urllib.request
import html5lib
import re
import datetime
import sys
import json

"""
Fetch single ETF data.
Source Etfdailynews.
"""
class ETFData:
    @staticmethod
    def convert_percent(pct):
        if type(pct) == float:
            return pct / 100
        return float(pct.rstrip('%')) / 100
    
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        self.name = None
        self.expense_ratio = None
        self.aum = None
        self.shares = None
        self.index = None
        self.report = None
        self.asset_class = None
        self.asset_class_size = None
        self.asset_class_style = None
        self.region_general = None
        self.region_specific = None
        self.holdings = None
        self.download_time = datetime.datetime.now()

        url = 'http://etfdb.com/etf/' + self.ticker + "/"
        try:
            html = urllib.request.urlopen(url).read()
        except urllib.error.HTTPError as e:
            if (e.code == 404):
                print(url + " not fund (404).")
            sys.exit()

        soup = bs(html, "html5lib")

        # Name
        self.name = soup.findAll("h1")[0].find_all("span")[
            1].get_text().strip()
        # Expense Ratio
        raw = soup.findAll("span", text=re.compile(r'Expense Ratio'))[
            0].findNext("span").get_text().strip()
        self.expense_ratio = self.convert_percent(raw)
        # AUM
        raw = soup.findAll("span", text=re.compile(r'AUM'))[
            0].findNext("span").get_text().strip().replace(",", "")
        self.aum = float(raw[1:-2])
        mul = raw[-1]
        if(mul == "B"):
            self.aum = self.aum * 1000000000
        elif(mul == "M"):
            self.aum = self.aum * 1000000
        # Shares
        raw = soup.findAll("span", text=re.compile(r'Shares:'))[
            0].findNext("span").get_text().strip()
        self.shares = float(raw[0:-2])
        mul = raw[-1]
        if(mul == "B"):
            self.shares = self.shares * 1000000000
        elif(mul == "M"):
            self.shares = self.shares * 1000000
        # Underlying Index
        self.index = soup.findAll("span", text=re.compile(r'Tracks This Index:'))[
            0].findNext("span").get_text()
        
        # ETFdb.com Report
        self.report = soup.find(id="analyst-collapse").findNext("p").get_text()

        # Asset Class
        self.asset_class = soup.findAll("span", text=re.compile(r'Asset Class:'))[
            0].findNext("span").get_text().strip()
        # Asset Class Size
        self.asset_class_size = soup.findAll("span", text=re.compile(r'Asset Class Size:'))[
            0].findNext("span").get_text().strip()
        # Asset Class Style
        self.asset_class_style = soup.findAll("span", text=re.compile(r'Asset Class Style:'))[
            0].findNext("span").get_text().strip()
        # Region (General)
        self.region_general = soup.findAll("span", text=re.compile(r'Region \(General\):'))[
            0].findNext("span").get_text().strip()
        # Region (Specific)
        self.region_specific = soup.findAll("span", text=re.compile(r'Region \(Specific\):'))[
            0].findNext("span").get_text().strip()
        
        # Holdings
        url = 'http://etfdailynews.com/tools/what-is-in-your-etf/?FundVariable=' + self.ticker
        html = urllib.request.urlopen(
            url).read().decode('cp1252').encode('utf-8')
        soup = bs(html, "html5lib")
        holdings_html = soup.find(id="etfs-that-own")
        holdings_table = "<table>" + \
            str(holdings_html.tbody).lstrip(
                "<tbody>").rstrip("</tbody>") + "</table>"
        holdings_df = pd.read_html(holdings_table)[0]
        holdings_df.columns = ['ticker', 'name', 'allocation']
        holdings_df['allocation'] = holdings_df.allocation.map(
            lambda x: self.convert_percent(x))
        self.holdings = holdings_df
        
    def printSummary(self):
        print("Ticker             " + self.ticker)
        print("Name               " + self.name)
        print("Expense ratio      {}".format(str(self.expense_ratio * 100) + '%'))
        print("AUM                {}".format(self.aum))
        print("Shares             {}".format(self.shares))
        print("NAV                {}".format(str(self.aum/self.shares) + '$'))
        print("Underlying Index   " + self.index)
        print("Asset class        " + self.asset_class)
        print("Asset class size   " + self.asset_class_size)
        print("Asset class style  " + self.asset_class_style)
        print("Region (generic)   " + self.region_general)
        print("Region (specific)  " + self.region_specific)
        print("Num. holdings      {}".format(str(self.holdings.shape[0])))
        print()
        print("Holdings")
        print(self.holdings)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python " + sys.argv[0] + " ticker")
        sys.exit(1)

    print("Downloading ETF details (" + sys.argv[0] + ")...")
    etf = ETFData(sys.argv[1])
    etf.printSummary()

    dump = json.dumps(etf)
    with open(sys.argv[1]+".json", 'w') as outfile:
        json.dump(etf, outfile)
