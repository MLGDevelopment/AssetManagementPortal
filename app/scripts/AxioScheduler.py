import threading
from threading import Thread
import time
import os
import sys
packages_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(os.path.join(packages_path, 'dbConn'))
sys.path.append(os.path.join(packages_path, 'Scraping'))
from axioDB import session, RentComp, AxioProperty, AxioPropertyOccupancy
from axioScraper import AxioScraper


def axio_scraper_scheduler(states=[], msas=[], asset_types=[], pause=0):
    """
    Function for managing Axio property updates
    """
    axio_scraper = AxioScraper(headless=True)
    axio_scraper.mlg_axio_login()

    kwags = {"states": [],
             "msas": [],
             "asset_types": [],
             }

    if (states and msas and asset_types) != []:
        all_property_data = AxioProperty.fetch_all_property_data
        if states:
            kwags["states"] = [i for i in states]
        if msas:
            kwags["msas"] = [i for i in msas]
        if asset_types:
            kwags["asset_types"] = [i for i in asset_types]
    else:
        p_ids = AxioProperty.fetch_all_property_ids()
        s_pids = [int(i) for i in p_ids]
        s_pids.sort()
        _id = str(s_pids.pop(0))
        axio_scraper.navigate_to_property_report(_id)
        for axio_id in s_pids:
            axio_id = str(axio_id)
            axio_scraper.navigate_to_property_report(axio_id)
            res = axio_scraper.get_property_data(axio_id, cache_res=True)
            if not res:
                exit(1)
            if pause:
                time.sleep(pause)


class AxioManager:

    def __init__(self, ):
        self.a_scraper_id = None
        self.a_scraper = Thread(target=axio_scraper_scheduler)
        self.a_scraper.daemon = True

    def running(self):
        return self.a_scraper.is_alive()

    def start_thread_if_not_running(self):
        is_running = self.running()
        if not is_running:
            self.a_scraper.start()
            self.a_scraper_id = self.a_scraper.ident
        return is_running


def main():
    axm = AxioManager()
    # axm.start_thread_if_not_running()
    axio_scraper_scheduler(pause=1)
    print


if __name__ == "__main__":
    main()
