import re

from uritemplate import expand, variables, TEMPLATE

EXCLUDE = ":/?#[]@!$&'()*+,;="
valid_template = "[^{}]+".format("\\".join(RESERVED))

def to_regex(template):
    return re.compile(re.sub(TEMPLATE, valid_template, template))
