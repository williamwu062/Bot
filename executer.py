from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import selenium
import time
import schedule
from datetime import datetime
from typing import Final
import configparser

timer = 0

class Target:
    LONG_WAIT: Final = 8
    AVG_WAIT: Final = 4
    SHORT_WAIT: Final = 2
    ERROR: Final = -1

    def __init__(self, username, password, DCPIs, PATH, cardnum=None, sec_code=None):
        self.order_status = 0
        self.access_count = 0
        self.PATH = PATH

        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        self.driver = webdriver.Chrome(PATH, options=options)
        self.driver.maximize_window()

        self.username = username
        self.password = password
        self.cardnum = cardnum
        self.sec_code = sec_code
        self.ACCESS_COUNTER = 0
        self.url_list = ["https://www.target.com/s?searchTerm=" + i for  i in DCPIs]

# order_status=0 is default, order_status=1 is preorder, order_status=2 is in stock


    def __fillForm(self, id, key, SUBMIT):
        if not SUBMIT:
            ele = self.driver.find_element_by_id(id)
            ele.clear()
            ele.send_keys(key)
        else:
            time.sleep(0.5)
            element = self.driver.find_element_by_id(id)
            element.clear()
            element.send_keys(key)
            time.sleep(0.5)
            self.driver.find_element_by_id('login').click()


    def __clicker(self, xpath=None, class_=None, click = True):
        staleElement = True
        while staleElement:
            try:
                if class_ == None:
                    button = self.driver.find_element_by_xpath(
                    xpath)
                else:
                    button = self.driver.find_element_by_class_name(class_)
                if button and click:
                    self.driver.execute_script("return arguments[0].scrollIntoView(true);", button)
                    button.click()
                elif button:
                    print(button.text)
                staleElement = False
            except selenium.common.exceptions.StaleElementReferenceException:
                print("exception")
                staleElement = True
            except selenium.common.exceptions.NoSuchElementException:
                return Target.ERROR

    def __addToCart(self, url):
        self.driver.get(url)
        # self.driver.implicitly_wait(LONG_WAIT if i == 0 else AVG_WAIT)
        self.driver.implicitly_wait(Target.AVG_WAIT)

        # searches and clicks product from search screen when searching DCPI

        if (order := self.__checkSearch()) is None:
            return Target.ERROR
        actions = ActionChains(self.driver)
        actions.click(order).perform()

        if self.__clicker(xpath='//button[@data-test="shipItButton"]') == Target.ERROR and \
                self.__clicker(xpath='//button[@data-test="addToCartModalContinueShopping"]') == Target.ERROR:
            print('error alert')
            return Target.ERROR

    def __checkout(self):
        self.__clicker(xpath='//button[@data-test="addToCartModalViewCartCheckout"]')
        self.__clicker(xpath='//button[@data-test="checkout-button"]')

    def buyFromTarget(self):
        global timer

        for i, url in enumerate(self.url_list):
            if self.__addToCart(url) == Target.ERROR and i == len(self.url_list) - 1:
                self.driver.get('https://www.target.com/co-cart')
            if i != len(self.url_list) - 1:
                self.driver.execute_script("window.open()")
                self.driver.switch_to.window(self.driver.window_handles[-1])
        self.__checkout()
        self.__fillForm('username', username, False)
        self.__fillForm('password', password, True)
        self.__clicker(xpath='//button[@data-test="placeOrderButton"]')
        print('time: ', timer-time.perf_counter())

    # Function first checks for link by class name. If not found, the function checks the link through a series of xpaths.
    # self.driver the selenium self.driver that was already initialized and set up with a url.
    def __checkSearch(self):
        # search_path = '//a[@data-test="product-title"]'
        search_path = '//button[@data-test="addButton"]'

        if self.driver.find_elements_by_xpath(search_path):
            print('found')
            search_button = self.driver.find_element_by_xpath(search_path)
            return search_button
        else:
            print('not found')
            return None

    def __checkStock(self):
        self.driver.get(self.url_list[0])
        self.driver.implicitly_wait(3)
        print(self.ACCESS_COUNTER)
        self.ACCESS_COUNTER += 1
        search_ret = self.__checkSearch()
        if search_ret is not None:
            return True
        return False

    def run(self):
        global timer
        timer = time.perf_counter()
        if self.__checkStock():
            schedule.clear()
            self.driver = webdriver.Chrome(self.PATH)
            self.driver.maximize_window()
            self.buyFromTarget()

if __name__ == '__main__':

    # tmp = datetime.now()
    # begin = tmp.replace(hour=int(0), minute=int(00))
    # end = tmp.replace(hour=int(1), minute=int(00))
    #
    # while True:
    #     tmp = datetime.now()
    #     if begin < tmp < end:
    #         break
    #     time.sleep(0.2)
    # print('past 12')
    #
    # now = datetime.now()
    # print(now)
    # start = now.replace(hour=int(9), minute=int(30))
    # print(start)
    #
    # while True:
    #     now = datetime.now()
    #     if now > start:
    #         break
    #     time.sleep(0.2)
    # print('yo')

    # "087-16-4919", "087-16-7462", "087-16-9980"
    # "087-16-2099", "087-16-2168"
    # ["087-16-4919", "087-16-7462", "087-16-9397", "087-16-9980"]
    # "087-16-7462", "087-16-9017", "087-16-8945", "087-16-9921", "087-16-4893"

    read_config = configparser.ConfigParser()
    read_config.read('private.ini')
    CHROME_PATH = read_config.get('DRIVER_PATH', 'PATH')
    username = read_config.get('LOGIN', 'username')
    password = read_config.get('LOGIN', 'password')
    dcpi_items = read_config.items('DCPI')
    dcpi_list = []
    for key, dcpi in dcpi_items:
        dcpi_list.append(dcpi)
    print(CHROME_PATH)
    print(username)
    print(password)
    print(dcpi_list)

    buy_instance = Target(username, password, dcpi_list, CHROME_PATH)

    schedule.every(6).seconds.do(lambda: buy_instance.run())


    while True:
        schedule.run_pending()
        # if not schedule.jobs:
        #     break
        time.sleep(1)