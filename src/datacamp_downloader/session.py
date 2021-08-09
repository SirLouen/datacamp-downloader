import json
import os
import pickle
from pathlib import Path

# import chromedriver_autoinstaller
import undetected_chromedriver.v2 as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .constants import HOME_PAGE, SESSION_FILE
from .datacamp_utils import Datacamp

# Check if the current version of chromedriver exists
# and if it doesn't exist, download it automatically,
# then add chromedriver to path
# chromedriver_autoinstaller.install()


class Session:
    def __init__(self) -> None:
        self.savefile = Path(SESSION_FILE)
        self.datacamp = self.load_datacamp()

    def save(self):
        self.datacamp.session = None
        pickled = pickle.dumps(self.datacamp)
        self.savefile.write_bytes(pickled)

    def load_datacamp(self):
        if self.savefile.exists():
            datacamp = pickle.load(self.savefile.open("rb"))
            datacamp.session = self
            return datacamp
        return Datacamp(self)

    def reset(self):
        try:
            os.remove(SESSION_FILE)
        except:
            pass

    def _setup_driver(self, headless=True):
        options = uc.ChromeOptions()
        options.headless = headless
        # just some options passing in to skip annoying popups
        options.add_argument(
            "--no-first-run "
            "--no-service-autorun "
            "--password-store=basic "
            "--disable-extensions "
            "--disable-browser-side-navigation "
            "--disable-dev-shm-usage "
            "--disable-infobars "
            "--disable-popup-blocking "
            "--disable-gpu "
            "--window-position=-10000,-10000 "
            "--disable-notifications "
            "--content-shell-hide-toolbar "
            "--top-controls-hide-threshold "
            "--force-app-mode "
            "--hide-scrollbars"
        )
        self.driver = uc.Chrome(options=options)
        # self.driver.minimize_window()

    def start(self, headless=True):
        if hasattr(self, "driver"):
            return
        self._setup_driver(headless)
        self.driver.get(HOME_PAGE)
        self.bypass_cloudflare(HOME_PAGE)
        if self.datacamp.token:
            self.add_token(self.datacamp.token)

    def bypass_cloudflare(self, url):
        try:
            self.get_element_by_id("cf-spinner-allow-5-secs")
            with self.driver:
                self.driver.get(url)
        except:
            pass

    def get(self, url):
        self.start()
        self.driver.get(url)
        self.bypass_cloudflare(url)
        return self.driver.page_source

    def get_json(self, url):
        page = self.get(url)
        page = self.driver.find_element(By.TAG_NAME, "pre").text
        parsed_json = json.loads(page)
        return parsed_json

    def get_element_by_id(self, id: str) -> WebElement:
        return self.driver.find_element(By.ID, id)

    def get_element_by_xpath(self, xpath: str) -> WebElement:
        return self.driver.find_element(By.XPATH, xpath)

    def click_element(self, id: str):
        self.get_element_by_id(id).click()

    def wait_for_element_by_css_selector(self, *css: str, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_any_elements_located((By.CSS_SELECTOR, ",".join(css)))
        )

    def add_token(self, token: str):
        cookie = {
            "name": "_dct",
            "value": token,
            "domain": ".datacamp.com",
            "secure": True,
        }
        self.driver.add_cookie(cookie)
        return self
