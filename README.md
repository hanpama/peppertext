# Peppertext

Declarative hypertext client

```python
from peppertext import Hypertext, resolve, register, selector

@register
class GoogleBlogPage(Hypertext):
    url = SimpleURLField(
        "https://googleblog.blogspot.kr/{year}/{month}/{title}.html"
    )

    title = selector.find(".title[itemprop=name]").text()
    body = selector.find(".post-body").text()

```

It resolves given headers, url and query string to hypertext object.

```
>>> p = resolve("https://googleblog.blogspot.kr/2015/11/google-gobble-thanksgiving-trends-on.html")
>>> p
<GoogleBlogPage at 0x108a4d1f0 >

>>> p.fetch()
>>> p['title']
'Google gobble: Thanksgiving trends on Search'
>>> p['body']
'In just a few hours, people across the U.S. will be settling...'
```

You can create GoogleBlogPage object with profile variables which are declared as
fields in `GoogleBlogPage` class.


```
>>> p = GoogleBlogPage(
...     year="2015",
...     month="11",
...     title="google-gobble-thanksgiving-trends-on"
... )

>>> p.fetch()
>>> p['title']
'Google gobble: Thanksgiving trends on Search'
```
