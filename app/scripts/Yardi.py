# Author: Nik Burmeister
import time
import bs4
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import datetime


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


class Yardi:

    def __init__(self, headless=True):
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")

        try:
            self.driver = webdriver.Chrome(executable_path="app/scripts/chromedriver.exe", chrome_options=self.chrome_options)
        except:
            self.driver = webdriver.Chrome(executable_path="chromedriver.exe", chrome_options=self.chrome_options)

        self.base = ""
        self.set_mlg_prop_list()
        self.set_valiant_prop_list()

    def set_mlg_prop_list(self):
        # TODO: GRAB FROM DB
        self.mlg_prop_list = ["145",
                              "45",
                              "acctng",
                              "c001",
                              "c002",
                              "c003",
                              "c003a",
                              "c004",
                              "c006",
                              "c006a",
                              "c006i",
                              "c007",
                              "c008",
                              "c008oea",
                              "c009",
                              "mlg3"]

    def set_valiant_prop_list(self):
        self.valiant_prop_list = ["m001",
                                  "m002",
                                  "m003",
                                  "m004",
                                  "m005",
                                  "m006",
                                  "m007",
                                  "m008",
                                  "m009",
                                  "m010",
                                  "m011",
                                  "m012",
                                  "m013",
                                  "m014",
                                  "m015"
                                  "m016",
                                  "mlgowned",
                                  "mr",
                                  "pb",
                                  "pr",
                                  "st"]

    def login(self, username, password, login_link):
        """
        METHOD TO LOG INTO YARDI
        :param username:
        :param password:
        :param login_link:
        :return:
        """
        try:
            self.driver.get(login_link)
            username_field = self.driver.find_element_by_id("Username")
            username_field.clear()
            username_field.send_keys(username)
            self.driver.find_element_by_id("Password_Text").click()
            self.driver.find_element_by_id("Password").send_keys(password)
            self.driver.find_element_by_id("cmdLogin1").click()
            return 1
        except:
            return 0

    def valiant_yardi_login(self):
        yardi_login_url = "https://www.yardiasp13.com/47310settlement/pages/LoginAdvanced.aspx"
        self.base = "https://www.yardiasp13.com/47310settlement/pages/"
        valiant_username = "nburmeister"
        valiant_password = "Winter19!"
        return self.login(valiant_username, valiant_password, yardi_login_url)

    def mlg_yardi_login(self):
        yardi_login_url = "https://www.yardiasptx11.com/65876mlgcapital/pages/LoginAdvanced.aspx"
        self.base = "https://www.yardiasptx11.com/65876mlgcapital/pages/"
        mlg_username = "mlgco"
        mlg_password = "mgmt2019"
        return self.login(mlg_username, mlg_password, yardi_login_url)

    def T12_Month_Statement(self, property, book, account_tree, period_start, period_end):
        # TODO: CHECK IF LOGGED IN
        yardi_financial_analytics_url = self.base + "GlrepFinancial.aspx"
        self.driver.get(yardi_financial_analytics_url)
        self.driver.find_element_by_id("PropertyID_LookupCode").clear()
        self.driver.find_element_by_id("PropertyID_LookupCode").send_keys(property)
        self.driver.find_element_by_id("BookID_LookupCode").clear()
        self.driver.find_element_by_id("BookID_LookupCode").send_keys(book)
        self.driver.find_element_by_id("TreeID_LookupCode").clear()
        self.driver.find_element_by_id("TreeID_LookupCode").send_keys(account_tree)
        self.driver.find_element_by_id("FromMMYY_TextBox").clear()
        self.driver.find_element_by_id("FromMMYY_TextBox").send_keys(period_start)
        self.driver.find_element_by_id("ToMMYY_TextBox").clear()
        self.driver.find_element_by_id("ToMMYY_TextBox").send_keys(period_end)
        self.driver.find_element_by_id("Display_Button").click()

        soup = BeautifulSoup(self.driver.page_source)
        financials = soup.find(id="TableWriter1")

        headers = []
        data = []

        for index, row in enumerate(financials.findAll('tr')):
            if index == 0:
                t_headers = financials.findAll('tr')[0].find_all('th')
                for h in t_headers:
                    headers.append(h.text.strip())
            else:
                line_item = row.findAll('td')
                line_data = []
                for i in line_item:
                    if isinstance(i, bs4.element.Tag):
                        try:
                            line_data.append(i.text.strip())
                        except AttributeError:
                            print("")
                data.append(line_data)

        df = pd.DataFrame(data=data)
        df.columns = ["Item",
                      "Jan 2019",
                      "Feb 2019",
                      "Mar 2019",
                      "Apr 2019",
                      "May 2019",
                      "Jun 2019",
                      "Jul 2019",
                      "Aug 2019",
                      "Sep 2019",
                      "Oct 2019",
                      "Nov 2019",
                      "Dec 2019",
                      "Total"]
        df = df.set_index("Item")
        return df

    def get_multifamily_stats(self, yardi_property_id, as_of_date):
        yardi_residential_reports_url = self.base + "ResReportSummary.aspx"
        self.driver.get(yardi_residential_reports_url)
        time.sleep(2)
        self.driver.find_element_by_css_selector("#ReportType_DropDownList").send_keys("Unit Statistic \nselect")
        self.driver.find_element_by_css_selector("#PropLookup_LookupCode").clear()
        self.driver.find_element_by_css_selector("#PropLookup_LookupCode").send_keys(yardi_property_id)
        self.driver.find_element_by_css_selector("#Date2_TextBox").clear()
        self.driver.find_element_by_css_selector("#Date2_TextBox").send_keys(str(as_of_date))
        self.driver.find_element_by_css_selector("#Display_Button").click()
        time.sleep(2)

        soup = BeautifulSoup(self.driver.page_source)
        unit_stats = soup.find_all('table')[1]
        rows = unit_stats.find_all('tr')[3:]

        headers = [i.text for i in rows[0].find_all('th')]
        records = []
        for row in rows:
            columns = row.find_all('td')
            if columns:
                record = []
                for column in columns:
                    record.append(column.text.strip())
                if len(record) == len(headers):
                    records.append(record)


        occupancy = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[2]/table/tbody/tr[4]/td[3]")
        occupancy = float(occupancy.text)/100
        market_rent = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[1]/table/tbody/tr[16]/td[7]")
        market_rent = float(market_rent.text)
        occupied_rent = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[1]/table/tbody/tr[16]/td[8]")
        occupied_rent = float(occupied_rent.text)

        self.driver.find_element_by_css_selector("#ReportType_DropDownList").send_keys("Projected Occupancy \nselect")
        self.driver.find_element_by_css_selector("#Display_Button").click()
        _60_day_trend = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[1]/table/tbody/tr[11]/td[6]")
        _60_day_trend = float(_60_day_trend.text) / 100
        self.driver.find_element_by_css_selector("#ReportType_DropDownList").send_keys("Aged Receivables \nselect")
        time.sleep(.75)
        self.driver.find_element_by_css_selector("#SummarizeBy_DropDownList").send_keys("Property \nselect")
        time.sleep(.75)
        self.driver.find_element_by_css_selector("#Display_Button").click()
        time.sleep(2.25)
        _30_day_ar = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[1]/table/tbody/tr[6]/td[4]")
        _30_day_ar = float(_30_day_ar.text.replace(",", ""))
        _all_ar = self.driver.find_element_by_xpath("/html/body/form/div[5]/div[1]/table/tbody/tr[6]/td[9]")
        _all_ar = float(_all_ar.text.replace(",", ""))

        res = {"occupancy": occupancy,
               "60_day_trend": _60_day_trend,
               "occupied_rent": occupied_rent,
               "market_rent": market_rent,
               "30_day_AR": _30_day_ar,
               "total_AR": _all_ar}

        return res

    def pull_multifamily_stats(self):
        from app.models import Property
        properties = Property.query.filter(Property.yardi_id != 'nan')
        start = '1/1/2019'
        end = '8/24/2020'
        t_span = pd.date_range(start, end, freq='2W').strftime("%m/%d/%Y").tolist()
        df = pd.DataFrame()
        for y_property in properties:
            for _date in t_span:
                res = self.get_multifamily_stats(y_property.yardi_id, _date)
                res["name"] = y_property.name
                res["period_ending"] = _date
                df.append(res, ignore_index=True)


def main():
    yardi_manager = Yardi(headless=True)
    yardi_manager.valiant_yardi_login()
    yardi_manager.pull_multifamily_stats()



if __name__ == '__main__':
    main()
