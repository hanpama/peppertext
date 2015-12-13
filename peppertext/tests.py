#-*-coding:utf-8-*-

from datetime import datetime
from unittest import TestCase

from pyquery import PyQuery as pq

from peppertext import base


class SelectorTestCase(TestCase):

    def test_initialized_selectors_chained(self):
        root_selector = base.selector
        self.assertIsInstance(root_selector, base.Selector)
        self.assertEqual(root_selector.previous_selector, None)

        find_selector = root_selector.find('a')
        self.assertIsInstance(find_selector, base.FindSelector)
        self.assertEqual(find_selector.previous_selector, root_selector)

        attr_selector = find_selector.attribute('href')
        self.assertIsInstance(attr_selector, base.AttributeSelector)
        self.assertEqual(attr_selector.previous_selector, find_selector)


    def test_get_attribute_with_selector_object(self):
        # Retrieve plain attribute in objects
        base.selector.select
        base.selector.set_args

        with self.assertRaises(AttributeError):
            base.selector.manoha

    def test_select_on_a_single_element(self):
        document = pq('<a href="http://example.com">')
        link_selector = base.selector.find('a').attribute('href')
        link = link_selector.select(document)

        self.assertEqual(link, "http://example.com")

    def test_select_on_multiple_elements(self):
        document = pq("""<div>
            <a href="http://example.com">Link1</a>
            <a href="http://example.com/dahokan">Link2</a>
            <a href="http://example.com/manoha">Link3</a>
        </div>""")

        find_selector = base.selector.find('a')
        selected_els = find_selector.select(document)
        self.assertEqual( [pq(el).attr["href"] for el in selected_els],
            [
                "http://example.com",
                "http://example.com/dahokan",
                "http://example.com/manoha"
            ]
        )

        attr_selector = find_selector.attribute('href', each=True)
        self.assertIsInstance(attr_selector, base.AttributeSelector)
        self.assertIsInstance(attr_selector.previous_selector, base.FindSelector)
        self.assertTrue(attr_selector.each)

        link_hrefs = attr_selector.select(document)
        self.assertEqual(link_hrefs,
            [
                "http://example.com",
                "http://example.com/dahokan",
                "http://example.com/manoha"
            ]
        )

class DateFormatFieldTestCase(TestCase):

    def test_date_format_field(self):
        field = base.DateFormatField("date", "%Y%m%d")

        self.assertEqual(field.variables, ["date"])

        self.assertTrue(field.match("20150101"))
        self.assertTrue(field.match("02151230"))

        self.assertFalse(field.match("2015-12-21"))

        self.assertEqual(field.expand(date=datetime(2015, 12, 31)), "20151231")

        parsed = field.parse("19721017")
        self.assertEqual(parsed, {
            "date": datetime(1972, 10, 17)
        })

        with self.assertRaises(base.FieldError):
            field.parse("19521301") # Invalid date

        with self.assertRaises(base.FieldError):
            field.parse("1954-13-01") # Invalid format

class SimpleURLFieldTestCase(TestCase):

    def test_common_field(self):
        field = base.SimpleURLField("{protocol}://{host}")

        self.assertEqual(field.variables, ["protocol", "host"])

        self.assertTrue(field.match("http://example.com/"))
        self.assertTrue(field.match("http://example.com"))

        self.assertTrue(field.match("http://manoha.example.com/"))
        self.assertFalse(field.match("http://example.com/manoha!"))
        self.assertFalse(field.match("http://exampl!e.com/"))
        self.assertFalse(field.match("http://exampl!edcom/"))

        self.assertEqual(
            field.expand(protocol="http", host="example.com"),
            "http://example.com"
        )

        parsed = field.parse("http://example.com")
        self.assertEqual(parsed, {
            "protocol": "http", "host": "example.com"
        })

        with self.assertRaises(base.FieldError):
            field.parse("http://something.is.missing.com/manoha")

    def test_common_field_with_static_url(self):
        field = base.SimpleURLField(
            "http://info.cern.ch/hypertext/WWW/TheProject.html"
        )
        self.assertTrue(
            field.match("http://info.cern.ch/hypertext/WWW/TheProject.html")
        )
        self.assertFalse(
            field.match("http://info.cern.ch/hypertext/WWW/TheProject")
        )
        self.assertFalse(
            field.match("http://info.cern.ch/hypertext/WWW/TheProject.html/foo")
        )

    def test_common_field_with_more_complex_url(self):
        field = base.SimpleURLField(
            "https://googleblog.blogspot.kr/{year}/{month}/{title}.html"
        )
        self.assertEqual(field.variables, ["year", "month", "title"])

        url = "https://googleblog.blogspot.kr/2015/11/google-gobble-thanksgiving-trends-on.html"
        profile_vars = {
            "year": "2015",
            "month": "11",
            "title": "google-gobble-thanksgiving-trends-on"
        }
        self.assertTrue(field.match(url))
        self.assertTrue(field.parse(url), profile_vars)
        self.assertTrue(field.expand(**profile_vars), url)


base.register(base.Hypertext)

@base.register
class W3Page(base.Hypertext):
    url = base.SimpleURLField(
        "http://info.cern.ch/hypertext/WWW/TheProject.html"
    )

@base.register
class GoogleBlogPage(base.Hypertext):
    url = base.SimpleURLField(
        "https://googleblog.blogspot.kr/{year}/{month}/{title}.html"
    )

    title = base.selector.find(".title[itemprop=name]").text()
    body = base.selector.find(".post-body").text()

@base.register
class KindsArticlePage(base.Hypertext):
    url = base.SimpleURLField(
        "http://www.mediagaon.or.kr/jsp/sch/mnews/newsView.jsp"
    )
    params = {
        "newsId": base.EntityField("newsId")
    }

    title = base.selector.find('.title').text()

@base.register
class KindsSearchPage(base.Hypertext):
    url = base.SimpleURLField(
        "http://www.mediagaon.or.kr/jsp/sch/mnews/search.jsp"
    )
    params = {
        "collection": "mkind",
        "startDate": base.EntityField("start_date"),
        "endDate": base.EntityField("end_date"),
        # "prefixQuery": 'base.CustomParam("prefix_query")',
        "query": "",
        "searchField": "Subject,Contents,Writer",
        "sortField": "DATE/DESC,RANK/DESC",
    }

    links = base.selector.find('a').attribute("href", each=True)



class BasicHypertextTestCase(TestCase):

    def test_parse_example_webpages(self):

        page = base.resolve("http://example.com")
        self.assertIsInstance(page, base.Hypertext)

        page.fetch()
        links = page["links"]
        self.assertEqual(len(links), 1)
        self.assertEqual("http://www.iana.org/domains/example", links[0])


    def test_parse_cern(self):
        page = base.resolve("http://info.cern.ch")
        self.assertIsInstance(page, base.Hypertext)

        page.fetch()
        links = page["links"]
        self.assertEqual(len(links), 4)
        self.assertEqual(
            [ item for item in links ],
            [
                "http://info.cern.ch/hypertext/WWW/TheProject.html",
                "http://line-mode.cern.ch/www/hypertext/WWW/TheProject.html",
                "http://home.web.cern.ch/topics/birth-web",
                "http://home.web.cern.ch/about"
            ]
        )

    def test_raise_exception_on_implicit_fetching(self):
        page = base.resolve("http://example.com")

        with self.assertRaises(base.NotFetchedYetError):
            page.get_links()

        with self.assertRaises(base.NotFetchedYetError):
            page.get_links(fetch=False)

    def test_cannot_parse_example_dot_com_with_post_method(self):
        with self.assertRaises(base.NotResolvedError):
            page = base.resolve("http://example.com", method="POST")

    def test_base_hypertext_does_not_parse_any_content(self):
        page = base.resolve("http://info.cern.ch")

        properties = page.get_properties(fetch=True)
        self.assertEqual(properties.keys(), {"links"})


class W3PageTestCase(TestCase):

    def test_registry(self):
        self.assertIn(W3Page, base.registry)

    def test_resolve_pagetype_with_url(self):
        p = base.resolve("http://info.cern.ch/hypertext/WWW/TheProject.html")
        self.assertIsInstance(p, W3Page)


class GoogleBlogPageTestCase(TestCase):

    def test_resolve_url_with_pattern_vars(self):
        p = base.resolve("https://googleblog.blogspot.kr/2015/11/google-gobble-thanksgiving-trends-on.html")
        self.assertIsInstance(p, GoogleBlogPage)

        #TODO: 나는 저거 url 패턴의 파라미터들을 어떻게 넘기려고 하는거지?

    def test_select_and_parse_properties(self):
        p = base.resolve("https://googleblog.blogspot.kr/2015/11/google-gobble-thanksgiving-trends-on.html")
        p.fetch()

        title = p.get_properties()["title"]
        body = p.get_properties()["body"]
        self.assertEqual(
            title, "Google gobble: Thanksgiving trends on Search"
        )
        self.assertTrue(body.startswith("In just a few hours"))

    def test_build_hypertext_instance_with_profile_vars(self):
        p = GoogleBlogPage(
            year="2015",
            month="11",
            title="google-gobble-thanksgiving-trends-on"
        )
        p.fetch()

        title = p.get_properties()["title"]
        body = p.get_properties()["body"]
        self.assertEqual(
            title, "Google gobble: Thanksgiving trends on Search"
        )
        self.assertTrue(body.startswith("In just a few hours"))

class KindsArticlePageTestCase(TestCase):
    def test_resolve_with_params_and_parse_properties(self):
        p = base.resolve(
            "http://www.mediagaon.or.kr/jsp/sch/mnews/newsView.jsp",
            params={"newsId": "01100101.20151102100000159"}
        )
        self.assertIsInstance(p, KindsArticlePage)

        p.fetch()
        title = p.get_properties()["title"]
        self.assertEqual(
            title, "[한·중·일 정상회의] 3국 정상, 회의 전엔 ‘미소 촬영’ 회견 땐 웃음기 ‘싹’…비빔밥으로 만찬"
        )

    def test_cannot_resolve_with_wrong_params_dict(self):
        # Ommitted params
        p = base.resolve("http://www.mediagaon.or.kr/jsp/sch/mnews/newsView.jsp")
        self.assertNotIsInstance(p, KindsArticlePage)

        with self.assertRaises(base.NotResolvedError):
            # Params not declared in pagetype
            base.resolve(
                url="http://www.mediagaon.or.kr/jsp/sch/mnews/newsView.jsp",
                params={"foo": "bar"}
            )

        # Wrong params does not raise NotResolvedError
        base.resolve(
            url="http://www.mediagaon.or.kr/jsp/sch/mnews/newsView.jsp",
            params={"newsId": "bar"}
        )

    def test_build_hypertext_with_params(self):
        p = KindsArticlePage(newsId="01100101.20151102100000159")

        p.fetch()
        title = p.get_properties()["title"]
        self.assertEqual(
            title, "[한·중·일 정상회의] 3국 정상, 회의 전엔 ‘미소 촬영’ 회견 땐 웃음기 ‘싹’…비빔밥으로 만찬"
        )

class KindsSearchPageTestCase(TestCase):

    def test_resolve_with_multiple_params(self):
        p = base.resolve(
            url="http://www.mediagaon.or.kr/jsp/sch/mnews/search.jsp",
            params = {
                "startDate": "2015.01.01",
                "endDate": "2015.10.05",
            }
        )
        self.assertIsInstance(p, KindsSearchPage)

        p.fetch()

        print(p["links"])
