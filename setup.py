from setuptools import setup, find_packages
from websampler import __version__

with open('requirements.txt') as req:
    install_requires = [ line for line in req if line ]

setup(
    name='peppertext',
    version=__version__,
    description='Declarative hypertext client',
    author='Kyungil Choi',
    author_email='hanpama@gmail.com',
    url='http://curlybrace.kr/',
    packages=[pkg for pkg in find_packages() if pkg.startswith('websampler')],
    include_package_data=True,
    long_description=open('README.rst').read(),
    classifiers=[
        'Programming Language :: Python :: 3.4',
    ],
    install_requires=install_requires,
    zip_safe=False,
)
