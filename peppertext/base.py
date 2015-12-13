"""
Peppertext :: Simple Hypertext Parser
=====================================

.. code-block:: python
   from peppertext import Hypertext, SimpleURLField, resolve

   class ExampleArticleListPage(Hypertext):
       url = SimpleURLField("http://example.com/articles/({year}")
       method = "GET"

..
   >>> page = resolve("http://example.com/articles/2015")
   >>> page
   <ExampleArticleListPage at 0x108a4d1f0 >

   >>> page.fetch()
   >>> page['links']
   ["http://info.cern.ch/hypertext/WWW/TheProject.html",
    "http://line-mode.cern.ch/www/hypertext/WWW/TheProject.html",
    "http://home.web.cern.ch/topics/birth-web",
    "http://home.web.cern.ch/about"]

"""
from copy import copy
from datetime import datetime
import re

import requests
from pyquery import PyQuery as pq
from six import add_metaclass

class NotFetchedYetError(Exception): pass
class InvalidProfilePassedError(TypeError): pass
class FieldError(Exception): pass
class NotResolvedError(Exception): pass


selector_registry = dict()

class SelectorBase(type):
    def __init__(cls, name, bases, nmspc):
        super(SelectorBase, cls).__init__(name, bases, nmspc)

        if not cls.name:
            cls.name = name.lower()

@add_metaclass(SelectorBase)
class Selector(object):
    """
    Document processing pipeline which can be chained.
    """
    name = "selector"

    def __getattribute__(self, key):
        try:
            plain_attr = super(Selector, self).__getattribute__(key)
            return plain_attr
        except AttributeError:
            if key in selector_registry:
                selector = selector_registry[key](self)
                return selector
            else:
                raise AttributeError("%s object has no attribute %s"%(self, key))

    def __init__(self, previous_selector=None):
        """
        Each selector must be initailized when referred as previous_selector's
        member given the previous_selector as a parameter.
        """
        self.previous_selector = previous_selector

    def __call__(self, *args, **kwargs):
        self.set_args(*args, **kwargs)
        return self

    def set_args(self, *args, **kwargs):
        pass

    def filter(self, document):
        return document

    def select(self, document):
        if self.previous_selector:
            document = self.previous_selector.select(document)

        return self.filter(document)

selector = Selector()

def register_selector(cls):
    selector_registry[cls.name] = cls
    return cls

@register_selector
class FindSelector(Selector):
    """
    Basic selector which initialized with css selector
    """
    name = "find"
    def set_args(self, css_selector, each=False):
        """
        css_selector:
           css selector string

        each:
           apply filter iterating document's elements.
           If this value is `False`, filter is applied to the first elements.
        """
        self.css_selector = css_selector
        self.each = each

    def filter(self, document):
        return pq(document)(self.css_selector)

@register_selector
class AttributeSelector(Selector):
    name = "attribute"

    def set_args(self, attribute_name, each=False):
        self.attribute_name = attribute_name
        self.each = each

    def filter(self, document):
        if self.each:
            return ([pq(el).attr[self.attribute_name] for el in document])
        return pq(document).attr[self.attribute_name]

@register_selector
class TextSelector(Selector):
    name = "text"

    def set_args(self, each=False):
        self.each = each

    def filter(self, document):
        if self.each:
            return ([pq(el).text() for el in document])
        return pq(document).text()

@register_selector
class AtSelector(Selector):
    name = "at"
    def set_args(self, index):
        self.index = index

    def filter(self, document):
        return pq(document).eq(self.index)

@register_selector
class RegexSubSelector(Selector):
    name = "sub"
    def set_args(self, pattern, repl=''):
        self.pattern = pattern
        self.repl = repl

    def filter(self, document):
        return re.sub(self.pattern, self.repl, document)

@register_selector
class CastSelector(Selector):
    name = "cast"
    def set_args(self, function):
        self.function = function

    def filter(self, document):
        return self.function(document)

class Field(object):
    pass

class EntityField(Field):
    """
    Parse string as a single value with name
    """
    def __init__(self, name):
        self.name = name

    def match(self, string):
        return True

    @property
    def variables(self):
        return [self.name]

    def expand(self, **kwargs):
        return kwargs[self.name]

    def parse(self, string):
        return {self.name: string}

class DateFormatField(Field):
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern

    def match(self, datetime_as_string):
        try:
            datetime.strptime(datetime_as_string, self.pattern)
            return True
        except ValueError:
            return False

    @property
    def variables(self):
        return [self.name]

    def expand(self, **kwargs):
        dd = kwargs[self.name]
        return dd.strftime(self.pattern)

    def parse(self, datetime_as_string):
        try:
            return {
                self.name: datetime.strptime(datetime_as_string, self.pattern)
            }
        except ValueError:
            raise FieldError("time data {} does not match format {}".format(
                datetime_as_string, self.pattern
            ))


class SimpleURLField(Field):
    """
    """
    def __init__(self, pattern):
        self.pattern = pattern

    def match(self, string):
        valid_template = "[^{}]+?/?".format("\\".join(":/?#[]@!$&'()*+,;="))
        regex_pattern = re.sub("{\w+}", valid_template, self.pattern)
        regex_pattern += "$"
        return re.match(regex_pattern, string)

    @property
    def variables(self):
        return re.findall("{(\w+)}", self.pattern)

    def expand(self, **kwargs):
        return self.pattern.format(**kwargs)

    def parse(self, string):
        if not self.match(string):
            raise FieldError("Cannot parse invalid string: {}".format(string))

        valid_template = "(?P<{var}>[^\:\/\?\#\[\]\@\!\$\&\'\(\)\*\+\,\;\=]+)/?"
        regex_pattern = self.pattern
        for item in self.variables:
            regex_pattern = re.sub(
                "{\w+}", valid_template.format(var=item), regex_pattern, 1
            )

        return re.fullmatch(regex_pattern, string).groupdict()

class HypertextBase(type):
    def __init__(cls, name, bases, nmspc):
        super(HypertextBase, cls).__init__(name, bases, nmspc)

        cls.selectors = {
            key: value for key, value in cls.__dict__.items()
            if isinstance(value, Selector)
        }

        cls.param_fields = {
            fieldname: value for fieldname, value in cls.params.items()
            if isinstance(value, Field)
        }

        cls.profile = cls.url.variables
        for param in cls.params.values():
            if not isinstance(param, Field):
                continue
            cls.profile.extend(param.variables)


@add_metaclass(HypertextBase)
class Hypertext(object):
    """
    Basic web page parser which catches any url with GET method.
    """
    url = EntityField("url")
    method = 'GET'
    params = {}
    data = ""

    links = selector.find('a').attribute('href', each=True)

    def __init__(self, data=None, **kwargs):
        self.profile_vars = kwargs
        self._links = None
        self._properties = None

    def expand(self):
        url = self.__class__.url.expand(**self.profile_vars)
        method = self.__class__.method
        params = copy(self.__class__.params)
        params.update({
            key: field.expand(**self.profile_vars)
            for key, field in self.__class__.param_fields.items()
        })
        return {"url": url, "method": method, "params": params}

    def fetch(self):
        # Expading profile to params
        self.response = requests.request(**self.expand())
        self.response.raise_for_status()

        self.bodytext = self.response.text
        self.document = pq(self.bodytext)

        # Property Parsing
        link_elements = self.document('a')
        self._links = [
            {"url": e.attrib.get("href", None), "method": "GET"}
            for e in link_elements
        ]
        self._properties = {
            name: selector.select(self.document)
            for name, selector in self.__class__.selectors.items()
        }

    def get_links(self, fetch=False):
        if self._links is not None:
            return self._links
        elif fetch:
            self.fetch()
            return self._links
        else:
            raise NotFetchedYetError("Cannot fetch implicitly")

    def get_properties(self, fetch=False):
        if self._properties is not None:
            return self._properties
        elif fetch:
            self.fetch()
            return self._properties
        else:
            raise NotFetchedYetError("Cannot fetch implicitly")

    def __getitem__(self, key):
        """
        Get a property in a dictionary-like way.
        It raises `NotFetchedYetError` if the properties is not fetched.
        """
        try:
            super(Hypertext, self).__getitem__(key)
        except AttributeError:
            return self.get_properties()[key]

    @classmethod
    def match(cls, url, method, params, headers):
        url_matched = cls.url.match(url)
        if not url_matched:
            return False

        method_matched = cls.method == method
        if not method_matched:
            return False

        params_matched = params.keys() == cls.param_fields.keys()
        if not params_matched:
            return False

        return True

    @classmethod
    def parse_profile(cls, url, method, params, headers):
        profile_vars = cls.url.parse(url)
        for key, field in cls.param_fields.items():
            profile_vars.update(
                field.parse(params[key])
            )
        return profile_vars


registry = []

def register(cls):
    registry.insert(0, cls)
    return cls

def resolve(url, method="GET", params={}, headers={}, data=None):
    """
    lookup every page type in register matching with given parameter
    and return matched one.
    """
    for hypertext in registry:
        if not hypertext.match(url, method, params, headers):
            continue
        # find all regex patterns and their values and pass them to constructor
        profile_vars = hypertext.parse_profile(url, method, params, headers)
        return hypertext(data=data, **profile_vars)

    raise NotResolvedError("Failed to resolve given link with url({})".format(url))
