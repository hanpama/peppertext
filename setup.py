from setuptools import setup, find_packages

with open('requirements.txt') as req:
    install_requires = [ line for line in req if line ]

setup(
    name='peppertext',
    version="0.1.0",
    description='Declarative hypertext client',
    author='Kyungil Choi',
    author_email='hanpama@gmail.com',
    url='http://curlybrace.kr/',
    packages=find_packages(),
    include_package_data=True,
    long_description=open('README.md').read(),
    classifiers=[
        'Programming Language :: Python :: 3.4',
    ],
    install_requires=install_requires,
    zip_safe=False,
)
