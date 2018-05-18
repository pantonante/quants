from bs4 import BeautifulSoup as bs
import ast
import datetime
import html5lib
import numpy as np
import pandas as pd
import re
import urllib.request
import sys
import json
from jsonmerge import merge

"""
Fetch single ETF data.
Sources: etfdb.com, Etfdailynews.com and zacks.com.
"""
class ETF:
    def __init__(self, ticker):
        self.isValid = False
        self.ticker = ticker.upper()
        self.name = None
        self.expense_ratio = None
        self.aum = None
        self.shares = None
        self.index = None
        self.asset_class = None
        self.category = None
        self.details = {}
        self.dataframes = {}

        url = 'http://etfdb.com/etf/' + self.ticker + "/"
        try:
            html = urllib.request.urlopen(url).read()
        except urllib.error.HTTPError as e:
            if (e.code == 404):
                print(url + " not fund (404).")
            sys.exit()
        soup = bs(html, "html5lib")

        # Name
        try:
            self.name = soup.findAll("h1")[0].find_all("span")[
                1].get_text().strip()
        except:
            print("Error getting name for " + self.ticker)

         # Expense Ratio
        try:
            raw = soup.findAll("span", text=re.compile(r'Expense Ratio'))[
                0].findNext("span").get_text().strip()
            self.expense_ratio = self.convert_percent(raw)
        except:
            print("Error getting Expense Ratio for " + self.ticker)

        # AUM
        try:
            raw = soup.findAll("span", text=re.compile(r'AUM'))[
                0].findNext("span").get_text().strip().replace(",", "")
            self.aum = float(raw[1:-2])
            mul = raw[-1]
            if(mul == "B"):
                self.aum = self.aum * 1000000000
            elif(mul == "M"):
                self.aum = self.aum * 1000000
        except:
            print("Error getting AUM for " + self.ticker)

        # Shares
        try:
            raw = soup.findAll("span", text=re.compile(r'Shares:'))[
                0].findNext("span").get_text().strip()
            self.shares = float(raw[0:-2])
            mul = raw[-1]
            if(mul == "B"):
                self.shares = int(
                    self.shares * 1000000000)
            elif(mul == "M"):
                self.shares = int(self.shares * 1000000)
        except:
            print("Error getting Shares for " + self.ticker)

        # Underlying Index
        try:
            self.index = soup.findAll("span", text=re.compile(r'Tracks This Index:'))[
                0].findNext("span").get_text()
        except:
            print("Error getting Underlying Index for " + self.ticker)

        # ETFdb.com Report
        try:
            self.details['report'] = soup.find(
                id="analyst-collapse").findNext("p").get_text()
        except:
            pass

        # Category
        try:
            self.category = soup.findAll("span", text=re.compile(r'ETFdb.com Category:'))[
                0].findNext("span").get_text().strip()
        except:
            print("Error getting Asset class for " + self.ticker)

        # Asset Class
        try:
            self.asset_class = soup.findAll("span", text=re.compile(r'Asset Class:'))[
                0].findNext("span").get_text().strip()
        except:
            print("Error getting Asset class for " + self.ticker)

        # Region (General)
        try:
            self.details['region_general'] = soup.findAll("span", text=re.compile(r'Region \(General\):'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Region (Specific)
        try:
            self.details['region_specific'] = soup.findAll("span", text=re.compile(r'Region \(Specific\):'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Bond Type(s)
        try:
            self.details['bond_type'] = soup.findAll("span", text=re.compile(r'Bond Type\(s\):'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Bond Duration
        try:
            self.details['bond_duration'] = soup.findAll("span", text=re.compile(r'Bond Duration:'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Asset Class Size
        try:
            self.details['asset_class_size'] = soup.findAll("span", text=re.compile(r'Asset Class Size:'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Asset Class Style
        try:
            self.details['asset_class_style'] = soup.findAll("span", text=re.compile(r'Asset Class Style:'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Currency
        try:
            self.details['currency'] = soup.findAll("span", text=re.compile(r'Currency:'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Commodity Type
        try:
            self.details['commodity_type'] = soup.findAll("span", text=re.compile(r'Commodity Type:'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Commodity
        try:
            self.details['commodity'] = soup.findAll("span", text=re.compile(r'Commodity:'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Commodity Exposure
        try:
            self.details['commodity_exposure'] = soup.findAll("span", text=re.compile(r'Commodity Exposure:'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Sector (General)
        try:
            self.details['sector_general'] = soup.findAll("span", text=re.compile(r'Sector \(General\):'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Sector (Specific)
        try:
            self.details['sector_specific'] = soup.findAll("span", text=re.compile(r'Sector \(Specific\):'))[
                0].findNext("span").get_text().strip()
        except:
            pass

        # Graphs
        # Asset Allocation
        try:
            tbody = soup.findAll("h3", text=re.compile(
                r'Asset Allocation'))[0].findNext("table").tbody
            table = "<table>" + \
                str(tbody).lstrip(
                    "<tbody>").rstrip("</tbody>") + "</table>"
            self.dataframes['asset_allocation'] = pd.read_html(table)[0]
            self.dataframes['asset_allocation'].columns = [
                'category', 'allocation']
            self.dataframes['asset_allocation']['allocation'] = self.dataframes['asset_allocation'].allocation.map(
                lambda x: self.convert_percent(x))
        except:
            pass

        # Sector Breakdown | Bond Sector Breakdown
        try:
            tbody = soup.findAll("h3", text=re.compile(r'Sector Breakdown'))[
                0].findNext("table").tbody
            table = "<table>" + \
                str(tbody).lstrip(
                    "<tbody>").rstrip("</tbody>") + "</table>"
            self.dataframes['sector_breakdown'] = pd.read_html(table)[0]
            self.dataframes['sector_breakdown'].columns = [
                'sector', 'allocation']
            self.dataframes['sector_breakdown']['allocation'] = self.dataframes['sector_breakdown'].allocation.map(
                lambda x: self.convert_percent(x))
        except:
            pass

        # Bond Sector Breakdown
        try:
            tbody = soup.findAll("h3", text=re.compile(r'Bond Sector Breakdown'))[
                0].findNext("table").tbody
            table = "<table>" + \
                str(tbody).lstrip(
                    "<tbody>").rstrip("</tbody>") + "</table>"
            self.dataframes['sector_breakdown'] = pd.read_html(table)[0]
            self.dataframes['sector_breakdown'].columns = [
                'sector', 'allocation']
            self.dataframes['sector_breakdown']['allocation'] = self.dataframes['sector_breakdown'].allocation.map(
                lambda x: self.convert_percent(x))
        except:
            pass

        # Bond Detailed Sector Breakdown
        try:
            tbody = soup.findAll("h3", text=re.compile(
                r'Bond Detailed Sector Breakdown'))[0].findNext("table").tbody
            table = "<table>" + \
                str(tbody).lstrip(
                    "<tbody>").rstrip("</tbody>") + "</table>"
            self.dataframes['bond_detailed_sector_breakdown'] = pd.read_html(table)[
                0]
            self.dataframes['bond_detailed_sector_breakdown'].columns = [
                'sector', 'allocation']
            self.dataframes['bond_detailed_sector_breakdown']['allocation'] = self.dataframes['bond_detailed_sector_breakdown'].allocation.map(
                lambda x: self.convert_percent(x))
        except:
            pass

        # Coupon Breakdown
        try:
            tbody = soup.findAll("h3", text=re.compile(
                r'Coupon Breakdown'))[0].findNext("table").tbody
            table = "<table>" + \
                str(tbody).lstrip(
                    "<tbody>").rstrip("</tbody>") + "</table>"
            self.dataframes['coupon_breakdown'] = pd.read_html(table)[0]
            self.dataframes['coupon_breakdown'].columns = [
                'coupon', 'allocation']
            self.dataframes['coupon_breakdown']['allocation'] = self.dataframes['coupon_breakdown'].allocation.map(
                lambda x: self.convert_percent(x))
        except:
            pass

        # Credit Quality
        try:
            tbody = soup.findAll("h3", text=re.compile(
                r'Credit Quality'))[0].findNext("table").tbody
            table = "<table>" + \
                str(tbody).lstrip(
                    "<tbody>").rstrip("</tbody>") + "</table>"
            self.dataframes['credit_quality'] = pd.read_html(table)[0]
            self.dataframes['credit_quality'].columns = [
                'rank', 'allocation']
            self.dataframes['credit_quality']['allocation'] = self.dataframes['credit_quality'].allocation.map(
                lambda x: self.convert_percent(x))
        except:
            pass

        # Maturity Breakdown
        try:
            tbody = soup.findAll("h3", text=re.compile(
                r'Maturity Breakdown'))[0].findNext("table").tbody
            table = "<table>" + \
                str(tbody).lstrip(
                    "<tbody>").rstrip("</tbody>") + "</table>"
            self.dataframes['maturity_breakdown'] = pd.read_html(table)[0]
            self.dataframes['maturity_breakdown'].columns = [
                'maturity', 'allocation']
            self.dataframes['maturity_breakdown']['allocation'] = self.dataframes['maturity_breakdown'].allocation.map(
                lambda x: self.convert_percent(x))
        except:
            pass

        # Market Cap Breakdown
        try:
            tbody = soup.findAll("h3", text=re.compile(
                r'Market Cap Breakdown'))[0].findNext("table").tbody
            table = "<table>" + \
                str(tbody).lstrip(
                    "<tbody>").rstrip("</tbody>") + "</table>"
            self.dataframes['market_cap_breakdown'] = pd.read_html(table)[0]
            self.dataframes['market_cap_breakdown'].columns = [
                'cap', 'allocation']
            self.dataframes['market_cap_breakdown']['allocation'] = self.dataframes['market_cap_breakdown'].allocation.map(
                lambda x: self.convert_percent(x))
        except:
            pass

        # Region Breakdown
        try:
            tbody = soup.findAll("h3", text=re.compile(
                r'Region Breakdown'))[0].findNext("table").tbody
            table = "<table>" + \
                str(tbody).lstrip(
                    "<tbody>").rstrip("</tbody>") + "</table>"
            self.dataframes['region_breakdown'] = pd.read_html(
                table)[0]
            self.dataframes['region_breakdown'].columns = [
                'ragion', 'allocation']
            self.dataframes['region_breakdown']['allocation'] = self.dataframes['region_breakdown'].allocation.map(
                lambda x: self.convert_percent(x))
        except:
            pass

        # Market Tier Breakdown
        try:
            tbody = soup.findAll("h3", text=re.compile(
                r'Market Tier Breakdown'))[0].findNext("table").tbody
            table = "<table>" + \
                str(tbody).lstrip(
                    "<tbody>").rstrip("</tbody>") + "</table>"
            self.dataframes['market_tier_breakdown'] = pd.read_html(
                table)[0]
            self.dataframes['market_tier_breakdown'].columns = [
                'tier', 'allocation']
            self.dataframes['market_tier_breakdown']['allocation'] = self.dataframes['market_tier_breakdown'].allocation.map(
                lambda x: self.convert_percent(x))
        except:
            pass

        # Country Breakdown
        try:
            tbody = soup.findAll("h3", text=re.compile(
                r'Country Breakdown'))[0].findNext("table").tbody
            table = "<table>" + \
                str(tbody).lstrip(
                    "<tbody>").rstrip("</tbody>") + "</table>"
            self.dataframes['country_breakdown'] = pd.read_html(
                table)[0]
            self.dataframes['country_breakdown'].columns = [
                'country', 'allocation']
            self.dataframes['country_breakdown']['allocation'] = self.dataframes['country_breakdown'].allocation.map(
                lambda x: self.convert_percent(x))
        except:
            pass

        # Holdings
        try:
            url = 'http://etfdailynews.com/tools/what-is-in-your-etf/?FundVariable=' + self.ticker
            html = urllib.request.urlopen(
                url).read().decode('cp1252').encode('utf-8')
            soup = bs(html, "html5lib")
            holdings_raw_table = soup.find(id="etfs-that-own")
            if(holdings_raw_table != None):
                holdings_tbody = holdings_raw_table.tbody
                holdings_table = "<table>" + \
                    str(holdings_tbody).lstrip("<tbody>").rstrip(
                        "</tbody>") + "</table>"
                self.dataframes['holdings'] = pd.read_html(holdings_table)[0]
                self.dataframes['holdings'].columns = [
                    'ticker', 'name', 'allocation']
                self.dataframes['holdings']['allocation'] = self.dataframes['holdings'].allocation.map(
                    lambda x: self.convert_percent(x))
        except:
            pass

        if('holdings' is not self.details.keys()):  # let's try with zacks.com
            '''
            Slower (since data is parsed from string) and less reliable data.
            '''
            try:
                url = 'https://www.zacks.com/funds/etf/' + ticker + '/holding'
                html = urllib.request.urlopen(url).read().decode('cp1252')
                str_start, str_end = html.find(
                    'etf_holdings.formatted_data = [ [ '), html.find(' ] ];')
                if str_start == -1 or str_end == -1:
                    # If Zacks does not have data for the given ETF
                    print("Could not fetch data for {}".format(ticker))
                else:
                    list_str = "[[" + html[(str_start + 34):str_end] + "]]"
                    holdings_list = ast.literal_eval(list_str)
                    self.dataframes['holdings'] = pd.DataFrame(holdings_list).drop(
                        2, 1).drop(4, 1).drop(5, 1)
                    self.dataframes['holdings'].columns = [
                        'name', 'ticker', 'allocation']
                    self.dataframes['holdings']['allocation'] = self.dataframes['holdings'].allocation.map(
                        lambda x: self.zacks_clean_allocation(x))
                    self.dataframes['holdings']['name'] = self.dataframes['holdings'].name.map(
                        lambda x: self.zacks_clean_name(x))
                    self.dataframes['holdings']['ticker'] = self.dataframes['holdings'].ticker.map(
                        lambda x: self.zacks_clean_ticker(x))
            except:
                pass

        self.isValid = True

    def __getitem__(self, key):
        if key in self.details.keys():
            return self.details[key]
        else:
            return None

    @staticmethod
    def convert_percent(pct):
        if type(pct) == float:
            return pct / 100
        return float(pct.rstrip('%')) / 100

    @staticmethod
    def zacks_clean_name(str_input):
        if "<span" in str_input:
            soup = bs(str_input, "lxml")
            return soup.find('span')['onmouseover'].lstrip("tooltip.show('").rstrip(".');")
        return str_input

    @staticmethod
    def zacks_clean_ticker(str_input):
        soup = bs(str_input, "lxml")
        return soup.find('a').text

    @staticmethod
    def zacks_clean_allocation(str_input):
        if str_input == "NA":
            return 0
        return float(str_input) / 100

    def getDetailsFields(self):
        return list(self.details.keys())

    def getTableFields(self):
        return list(self.dataframes.keys())

    def printSummary(self):
        print()
        print("Ticker             {}".format(self.ticker))
        print("Name               {}".format(self.name))
        print("Category           {}".format(self.category))
        print("Asset class        {}".format(self.asset_class))
        print("Expense ratio      {}".format(
            str(self.expense_ratio * 100) + '%'))
        print("AUM                {}".format(self.aum))
        print("Shares             {}".format(str(self.shares)))
        print("NAV                {0:.3f}$".format(
            self.aum/self.shares))
        print("Underlying Index   {}".format(self.index))
        if ("holdings" in self.dataframes.keys()):
            print("Num. holdings      {}".format(
                str(self.dataframes['holdings'].shape[0])))
        else:
            print("Holdings           NA")
        print()
        print("Details:            {}".format(str(self.getDetailsFields())))
        print("Tables:             {}".format(str(self.getTableFields())))
        print()

    class JsonEncoder(json.JSONEncoder):

        def default(self, obj):
            if hasattr(obj, 'to_json'):
                return obj.to_json(orient='records', force_ascii=False),
            return json.JSONEncoder.default(self, obj)

    def dataframesToDict(self):
        dict_obj = {}
        for key in self.dataframes.keys():
            dict_obj[key] = self.dataframes[key].to_dict(orient='records')
        return dict_obj

    def toJson(self):
        return json.dumps({
            'ticker': self.ticker,
            'name': self.name,
            'category': self.category,
            'asset_class': self.asset_class,
            'expense_ratio': self.expense_ratio,
            'aum': self.aum,
            'shares': self.shares,
            'index': self.index,
            'details': self.details, 'tables': self.dataframes
        }, cls=self.JsonEncoder)

    def toDict(self):
        return {
            'ticker': self.ticker,
            'name': self.name,
            'category': self.category,
            'asset_class': self.asset_class,
            'expense_ratio': self.expense_ratio,
            'aum': self.aum,
            'shares': self.shares,
            'index': self.index,
            'details': self.details, 'tables': self.dataframesToDict()
        }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python " + sys.argv[0] + " ticker")
        sys.exit(1)

    print("Downloading ETF details (" + sys.argv[1] + ")...")
    etf = ETF(sys.argv[1])
    etf.printSummary()
