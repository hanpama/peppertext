Peppertext
==========

Declarative hypertext client

.. code-block:: python

   from peppertext import Hypertext, resolve, register, selector

   @register
   class GoogleBlogPage(Hypertext):
       url = SimpleURLField(
           "https://googleblog.blogspot.kr/{year}/{month}/{title}.html"
       )

       title = selector.find(".title[itemprop=name]").text()
       body = selector.find(".post-body").text()


It resolves given headers, url and query string to hypertext object.

.. code-block:: python

   >>> p = resolve("https://googleblog.blogspot.kr/2015/11/google-gobble-thanksgiving-trends-on.html")
   >>> p
   <GoogleBlogPage at 0x108a4d1f0 >

   >>> p.fetch()
   >>> p['title']
   'Google gobble: Thanksgiving trends on Search'
   >>> p['body']
   'In just a few hours, people across the U.S. will be settling...'

You can create GoogleBlogPage object with profile variables which are declared as
fields in `GoogleBlogPage` class.


.. code-block:: python

   >>> p = GoogleBlogPage(
   ...     year="2015",
   ...     month="11",
   ...     title="google-gobble-thanksgiving-trends-on"
   ... )

   >>> p.fetch()
   >>> p['title']
   'Google gobble: Thanksgiving trends on Search'


Selectors
---------

.. code-block:: python

   class GoogleBlogPage(Hypertext):
       # ...
       title = selector.find(".title[itemprop=name]").text()
       # ...

Selectors process a document which is returned from server as response.
In the `GoogleBlogPage` example above, `title` selector parses document and
find an element specified with `".title[itemprop=name]"` css selector.
You can access the value title with subscribing the `GoogleBlogPage` object
with selector name.

.. code-block:: python

   document = pq("""<div>
       <a href="http://example.com">Link1</a>
       <a href="http://example.com/dahokan">Link2</a>
       <a href="http://example.com/manoha">Link3</a>
   </div>""")

   find_selector = selector.find('a')
   selected_els = find_selector.select(document)
   self.assertEqual( [pq(el).attr["href"] for el in selected_els],
       [
           "http://example.com",
           "http://example.com/dahokan",
           "http://example.com/manoha"
       ]
   )


`find`
""""""

Select html elements which match to given css selector string.

`attribute`
"""""""""""

Get an element's attribute value with given attribute name.

`text`
""""""

Select the html element's inner text value.

`at`
""""

Get an item on index

`sub`
"""""

.. code-block:: python

   sub_selector = selector.sub(pattern="\d+", repl="")

Do regex substitution.

`cast`
""""""

.. code-block:: python

   int_cast_selector = selector.cast(int)

Pass the data to the function given as a parameter.
