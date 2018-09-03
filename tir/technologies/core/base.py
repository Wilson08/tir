import re
import time
import unittest
import inspect
import socket
import sys
import os
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
import tir.technologies.core.enumerations as enum
from tir.technologies.core.log import Log
from tir.technologies.core.config import ConfigLoader
from tir.technologies.core.language import LanguagePack
from tir.technologies.core.third_party.xpath_soup import xpath_soup
from selenium.webdriver.firefox.options import Options as FirefoxOpt
from selenium.webdriver.chrome.options import Options as ChromeOpt

class Base(unittest.TestCase):
    """
    Base class for any technology to implement Selenium Interface Tests.

    This class instantiates the browser, reads the config file and prepares the log.

    If no config_path is passed, it will read the config.json file that exists in the same
    folder as the file that would execute this module.

    :param config_path: The path to the config file. - **Default:** "" (empty string)
    :type config_path: str

    Usage:

    The Base class must be inherited by every internal class of each technology that would exist in this module.

    The classes must be declared under pwa/technologies/ folder.

    >>> def WebappInternal(Base):
    >>> def APWInternal(Base):
    """
    def __init__(self, config_path=""):
        """
        Definition of each global variable:

        base_container: A variable to contain the layer element to be used on all methods.

        errors: A list that contains every error that should be sent to log at the end of the execution.

        language: Contains the terms defined in the language defined in config or found in the page.

        log: Object that controls the logs of the entire application.

        log.station: Property of the log that contains the machine's hostname.

        log_file: A variable to control when to generate a log file of each execution of web_scrap. (Debug purposes)

        wait: The global Selenium Wait defined to be used in the entire application.
        """
        if config_path == "":
            config_path = os.path.join(sys.path[0], r"config.json")
        self.config = ConfigLoader(config_path)

        if self.config.browser.lower() == "firefox":
            driver_path = os.path.join(os.path.dirname(__file__), r'drivers\\geckodriver.exe')
            log_path = os.path.join(os.path.dirname(__file__), r'geckodriver.log')
            options = FirefoxOpt()
            options.set_headless(self.config.headless)
            self.driver = webdriver.Firefox(firefox_options=options, executable_path=driver_path, log_path=log_path)
        elif self.config.browser.lower() == "chrome":
            driver_path = os.path.join(os.path.dirname(__file__), r'drivers\\chromedriver.exe')
            options = ChromeOpt()
            options.set_headless(self.config.headless)
            self.driver = webdriver.Chrome(chrome_options=options, executable_path=driver_path)

        self.driver.maximize_window()
        self.driver.get(self.config.url)

        #Global Variables:

        self.wait = WebDriverWait(self.driver,5)

        self.language = LanguagePack(self.config.language) if self.config.language else ""
        self.log = Log(folder=self.config.log_folder)
        self.log.station = socket.gethostname()

        self.base_container = "body"
        self.errors = []
        self.config.log_file = False

# Internal Methods

    def assert_result(self, expected):
        """
        [Internal]

        Asserts the result based on the expected value.

        :param expected: Expected value
        :type expected: bool

        Usage :

        >>> #Calling the method:
        >>> self.assert_result(True)
        """
        expected_assert = expected
        msg = "Passed"
        stack_item = next(iter(list(map(lambda x: x.function, filter(lambda x: re.search('test_', x.function), inspect.stack())))), None)
        test_number = f"{stack_item.split('_')[-1]} -" if stack_item else ""
        log_message = f"{test_number}"
        self.log.set_seconds()

        if self.errors:
            expected = not expected

            for field_msg in self.errors:
                log_message += (" " + field_msg)

            msg = log_message

            self.log.new_line(False, log_message)
        else:
            self.log.new_line(True, "")

        self.log.save_file()

        self.errors = []
        print(msg)
        if expected_assert:
            self.assertTrue(expected, msg)
        else:
            self.assertFalse(expected, msg)

    def click(self, element, click_type=enum.ClickType.JS):
        """
        [Internal]

        Clicks on the Selenium element.

        Supports three types of clicking: JavaScript, pure Selenium and Selenium's ActionChains.

        Default is JavaScript clicking.

        :param element: Selenium element
        :type element: Selenium object
        :param click_type: ClickType enum. - **Default:** enum.ClickType.JS
        :type click_type: enum.ClickType

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> self.click(element(), type=enum.ClickType.JS)
        """
        try:
            self.scroll_to_element(element)
            if click_type == enum.ClickType.JS:
                self.driver.execute_script("arguments[0].click()", element)
            elif click_type == enum.ClickType.SELENIUM:
                element.click()
            elif click_type == enum.ClickType.ACTIONCHAINS:
                ActionChains(self.driver).move_to_element(element).click().perform()
        except Exception as error:
            self.log_error(str(error))

    def compare_field_values(self, field, user_value, captured_value, message):
        """
        [Internal]

        Validates and stores field in the self.errors array if the values are different.

        :param field: Field name
        :type field: str
        :param user_value: User input value
        :type user_value: str
        :param captured_value: Interface captured value
        :type captured_value: str
        :param message: Error message if comparison fails
        :type message: str

        Usage:

        >>> #Calling the method
        >>> self.compare_field_values("A1_NOME", "JOÃO", "JOOÃ", "Field A1_NOME has different values")
        """
        if str(user_value).strip() != str(captured_value).strip():
            self.errors.append(message)

    def double_click(self, element):
        """
        [Internal]

        Clicks two times on the Selenium element.

        :param element: Selenium element
        :type element: Selenium object

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> self.double_click(element())
        """
        try:
            self.scroll_to_element(element)
            element.click()
            element.click()
        except Exception:
            self.scroll_to_element(element)
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            actions.double_click()
            actions.perform()

    def element_exists(self, term, scrap_type=enum.ScrapType.TEXT, position=0, optional_term="", main_container=".tmodaldialog,.ui-dialog"):
        """
        [Internal]

        Returns a boolean if element exists on the screen.

        :param term: The first term to use on a search of element
        :type term: str
        :param scrap_type: Type of element search. - **Default:** enum.ScrapType.TEXT
        :type scrap_type: enum.ScrapType
        :param position: Position which element is located. - **Default:** 0
        :type position: int
        :param optional_term: Second term to use on a search of element. Used in MIXED search. - **Default:** "" (empty string)
        :type optional_term: str

        :return: True if element is present. False if element is not present.
        :rtype: bool

        Usage:

        >>> element_is_present = element_exists(term=".ui-dialog", scrap_type=enum.ScrapType.CSS_SELECTOR)
        >>> element_is_present = element_exists(term=".tmodaldialog.twidget", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1)
        >>> element_is_present = element_exists(term=text, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay")
        """
        if self.debug_log:
            print(f"term={term}, scrap_type={scrap_type}, position={position}, optional_term={optional_term}")

        if scrap_type == enum.ScrapType.SCRIPT:
            return bool(self.driver.execute_script(term))
        elif (scrap_type != enum.ScrapType.MIXED and scrap_type != enum.ScrapType.TEXT):
            selector = term
            if scrap_type == enum.ScrapType.CSS_SELECTOR:
                by = By.CSS_SELECTOR
            elif scrap_type == enum.ScrapType.XPATH:
                by = By.XPATH

            if scrap_type != enum.ScrapType.XPATH:
                soup = self.get_current_DOM()
                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container
                containers = self.zindex_sort(soup.select(container_selector), reverse=True)
                container = next(iter(containers), None)
                if not container:
                    return False

                try:
                    container_element = self.driver.find_element_by_xpath(xpath_soup(container))
                except:
                    return False
            else:
                container_element = self.driver

            element_list = container_element.find_elements(by, selector)
        else:
            if scrap_type == enum.ScrapType.MIXED:
                selector = optional_term
            else:
                selector = "div"

            element_list = self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container)
        if position == 0:
            return len(element_list) > 0
        else:
            return len(element_list) >= position

    def filter_displayed_elements(self, elements, reverse=False):
        """
        [Internal]

        Receives a BeautifulSoup element list and filters only the displayed elements.

        :param elements: BeautifulSoup element list
        :type elements: List of BeautifulSoup objects
        :param reverse: Boolean value if order should be reversed or not. - **Default:** False
        :type reverse: bool

        :return: List of filtered BeautifulSoup elements
        :rtype: List of BeautifulSoup objects

        Usage:

        >>> #Defining the element list:
        >>> soup = self.get_current_DOM()
        >>> elements = soup.select("div")
        >>> #Calling the method
        >>> self.filter_displayed_elements(elements, True)
        """
        #1 - Create an enumerated list from the original elements
        indexed_elements = list(enumerate(elements))
        #2 - Convert every element from the original list to selenium objects
        selenium_elements = list(map(lambda x : self.driver.find_element_by_xpath(xpath_soup(x)), elements))
        #3 - Create an enumerated list from the selenium objects
        indexed_selenium_elements = list(enumerate(selenium_elements))
        #4 - Filter elements based on "is_displayed()" and gets the filtered elements' enumeration
        filtered_selenium_indexes = list(map(lambda x: x[0], filter(lambda x: x[1].is_displayed(), indexed_selenium_elements)))
        #5 - Use List Comprehension to build a filtered list from the elements based on enumeration
        filtered_elements = [x[1] for x in indexed_elements if x[0] in filtered_selenium_indexes]
        #6 - Sort the result and return it
        return self.zindex_sort(filtered_elements, reverse)

    def find_first_div_parent(self, element):
        """
        [Internal]

        Finds first div parent element of another BeautifulSoup element.

        If element is already a div, it will return the element.

        :param element: BeautifulSoup element
        :type element: BeautifulSoup object

        :return: The first div parent of the element
        :rtype: BeautifulSoup object

        Usage:

        >>> parent_element = self.find_first_div_parent(my_element)
        """
        current = element
        while(hasattr(current, "name") and current.name != "div"):
            current = current.find_parent()
        return current

    def find_label_element(self, label_text, container):
        """
        [Internal]

        Find input element next to label containing the label_text parameter.

        :param label_text: The label text to be searched
        :type label_text: str
        :param container: The main container object to be used
        :type container: BeautifulSoup object

        :return: A list containing a BeautifulSoup object next to the label
        :rtype: List of BeautifulSoup objects

        Usage:

        >>> self.find_label_element("User:", container_object)
        """
        element = next(iter(list(map(lambda x: self.find_first_div_parent(x), container.find_all(text=re.compile(f"^{re.escape(label_text)}" + r"(\*?)(\s*?)$"))))), None)
        if element is None:
            return []

        next_sibling = element.find_next_sibling("input")
        if next_sibling:
            return [next_sibling]
        else:
            return []

    def get_current_DOM(self):
        """
        [Internal]

        Returns current HTML DOM parsed as a BeautifulSoup object

        :returns: BeautifulSoup parsed DOM
        :rtype: BeautifulSoup object

        Usage:

        >>> #Calling the method
        >>> soup = self.get_current_DOM()
        """
        return BeautifulSoup(self.driver.page_source,"html.parser")

    def get_element_text(self, element):
        """
        [Internal]

        Gets element text.

        :param element: Selenium element
        :type element: Selenium object

        :return: Element text
        :rtype: str

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> text = self.get_element_text(element())
        """
        return self.driver.execute_script("return arguments[0].innerText", element)

    def get_element_value(self, element):
        """
        [Internal]

        Gets element value.

        :param element: Selenium element
        :type element: Selenium object

        :return: Element value
        :rtype: str

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> text = self.get_element_value(element())
        """
        return self.driver.execute_script("return arguments[0].value", element)

    def log_error(self, message, new_log_line=True):
        """
        [Internal]

        Finishes execution of test case with an error and creates the log information for that test.

        :param message: Message to be logged
        :type message: str
        :param new_log_line: Boolean value if Message should be logged as new line or not. - **Default:** True
        :type new_log_line: bool

        Usage:

        >>> #Calling the method:
        >>> self.log_error("Element was not found")
        """
        stack_item = next(iter(list(map(lambda x: x.function, filter(lambda x: re.search('test_', x.function), inspect.stack())))), None)
        test_number = f"{stack_item.split('_')[-1]} -" if stack_item else ""
        log_message = f"{test_number} {message}"
        self.log.set_seconds()

        if new_log_line:
            self.log.new_line(False, log_message)
        self.log.save_file()
        self.assertTrue(False, log_message)

    def move_to_element(self, element):
        """
        [Internal]

        Move focus to element on the screen.

        :param element: Selenium element
        :type element: Selenium object

        Usage:

        >>> #Defining an element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> self.scroll_to_element(element())
        """
        ActionChains(self.driver).move_to_element(element).perform()

    def scroll_to_element(self, element):
        """
        [Internal]

        Scroll to element on the screen.

        :param element: Selenium element
        :type element: Selenium object

        Usage:

        >>> #Defining an element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> self.scroll_to_element(element())
        """
        if element.get_attribute("id"):
            self.driver.execute_script("return document.getElementById('{}').scrollIntoView();".format(element.get_attribute("id")))
        else:
            self.driver.execute_script("return arguments[0].scrollIntoView();", element)

    def search_zindex(self,element):
        """
        [Internal]

        Returns zindex value of BeautifulSoup object.

        Internal function created to be used inside lambda of zindex_sort method.

        Only works if element has Style attribute.

        :param element: BeautifulSoup element
        :type element: BeautifulSoup object

        :return: z-index value
        :rtype: int

        Usage:

        >>> #Line extracted from zindex_sort method:
        >>> elements.sort(key=lambda x: self.search_zindex(x), reverse=reverse)

        """
        zindex = 0
        if hasattr(element,"attrs") and "style" in element.attrs and "z-index:" in element.attrs['style']:
            zindex = int(element.attrs['style'].split("z-index:")[1].split(";")[0].strip())

        return zindex

    def select_combo(self, element, option):
        """
        Selects the option on the combobox.

        :param element: Combobox element
        :type element: Beautiful Soup object
        :param option: Option to be selected
        :type option: str

        Usage:

        >>> #Calling the method:
        >>> self.select_combo(element, "Chosen option")
        """
        combo = Select(self.driver.find_element_by_xpath(xpath_soup(element)))
        value = next(iter(filter(lambda x: x.text[0:len(option)] == option, combo.options)), None)

        if value:
            time.sleep(1)
            combo.select_by_visible_text(value.text)
            print(f"Selected value for combo is: {value.text}")

    def send_keys(self, element, arg):
        """
        [Internal]

        Clicks two times on the Selenium element.

        :param element: Selenium element
        :type element: Selenium object
        :param arg: Text or Keys to be sent to the element
        :type arg: str or selenium.webdriver.common.keys

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method with a string
        >>> self.send_keys(element(), "Text")
        >>> #Calling the method with a Key
        >>> self.send_keys(element(), Keys.ENTER)
        """
        try:
            element.send_keys("")
            element.click()
            element.send_keys(arg)
        except Exception:
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            actions.send_keys("")
            actions.click()
            actions.send_keys(arg)
            actions.perform()

    def search_stack(self, function):
        """
        Returns True if passed function is present in the call stack.

        :param function: Name of the function
        :type function: str

        :return: Boolean if passed function is present or not in the call stack.
        :rtype: bool

        Usage:

        >>> # Calling the method:
        >>> is_present = self.search_stack("MATA020")
        """
        return len(list(filter(lambda x: x.function == function, inspect.stack()))) > 0

    def set_element_focus(self, element):
        """
        [Internal]

        Sets focus on element.

        :param element: Selenium element
        :type element: Selenium object

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> text = self.set_element_focus(element())
        """
        self.driver.execute_script("arguments[0].focus();", element)

    def web_scrap(self, term, scrap_type=enum.ScrapType.TEXT, optional_term=None, label=False, main_container=None):
        """
        [Internal]

        Returns a BeautifulSoup object list based on the search parameters.

        Does not support ScrapType.XPATH as scrap_type parameter value.

        :param term: The first search term. A text or a selector
        :type term: str
        :param scrap_type: The type of webscraping. - **Default:** enum.ScrapType.TEXT
        :type scrap_type: enum.ScrapType.
        :param optional_term: The second search term. A selector used in MIXED webscraping. - **Default:** None
        :type optional_term: str
        :param label: If the search is based on a label near the element. - **Default:** False
        :type label: bool
        :param main_container: The selector of a container element that has all other elements. - **Default:** None
        :type main_container: str

        :return: List of BeautifulSoup4 elements based on search parameters.
        :rtype: List of BeautifulSoup4 objects

        Usage:

        >>> #All buttons
        >>> buttons = self.web_scrap(term="button", scrap_type=enum.ScrapType.CSS_SELECTOR)
        >>> #----------------#
        >>> #Elements that contain the text "Example"
        >>> example_elements = self.web_scrap(term="Example")
        >>> #----------------#
        >>> #Elements with class "my_class" and text "my_text"
        >>> elements = self.web_scrap(term="my_text", scrap_type=ScrapType.MIXED, optional_term=".my_class")
        """
        try:
            endtime = time.time() + 60
            container =  None
            while(time.time() < endtime and container is None):
                soup = self.get_current_DOM()

                if self.config.log_file:
                    with open(f"{term + str(scrap_type) + str(optional_term) + str(label) + str(main_container) + str(random.randint(1, 101)) }.txt", "w") as text_file:
                        text_file.write(f" HTML CONTENT: {str(soup)}")

                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container

                containers = self.zindex_sort(soup.select(container_selector), reverse=True)

                container = next(iter(containers), None)

            if container is None:
                raise Exception("Couldn't find container")

            if (scrap_type == enum.ScrapType.TEXT):
                if label:
                    return self.find_label_element(term, container)
                else:
                    return list(filter(lambda x: term.lower() in x.text.lower(), container.select("div > *")))
            elif (scrap_type == enum.ScrapType.CSS_SELECTOR):
                return container.select(term)
            elif (scrap_type == enum.ScrapType.MIXED and optional_term is not None):
                return list(filter(lambda x: term.lower() in x.text.lower(), container.select(optional_term)))
            elif (scrap_type == enum.ScrapType.SCRIPT):
                script_result = self.driver.execute_script(term)
                return script_result if isinstance(script_result, list) else []
            else:
                return []
        except Exception as e:
            self.log_error(str(e))

    def zindex_sort (self, elements, reverse=False):
        """
        [Internal]

        Sorts list of BeautifulSoup elements based on z-index style attribute.

        Only works if elements have Style attribute.

        :param elements: BeautifulSoup element list
        :type elements: List of BeautifulSoup objects
        :param reverse: Boolean value if order should be reversed or not. - **Default:** False
        :type reverse: bool

        :return: List of sorted BeautifulSoup elements based on zindex.
        :rtype: List of BeautifulSoup objects

        Usage:

        >>> #Defining the element list:
        >>> soup = self.get_current_DOM()
        >>> elements = soup.select("div")
        >>> #Calling the method
        >>> self.zindex_sort(elements, True)
        """
        elements.sort(key=lambda x: self.search_zindex(x), reverse=reverse)
        return elements

# User Methods

    def AssertFalse(self):
        """
        Defines that the test case expects a False response to pass

        Usage:

        >>> #Calling the method
        >>> self.AssertFalse()
        """
        self.assert_result(False)

    def AssertTrue(self):
        """
        Defines that the test case expects a True response to pass

        Usage:

        >>> #Calling the method
        >>> self.AssertTrue()
        """
        self.assert_result(True)

    def TearDown(self):
        """
        Closes the webdriver and ends the test case.

        Usage:

        >>> #Calling the method
        >>> self.TearDown()
        """
        self.driver.close()