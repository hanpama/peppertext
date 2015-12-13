from setuptools import setup, find_packages


setup(
    name='peppertext',
    version="0.1.2",
    description='Declarative hypertext client',
    author='Kyungil Choi',
    author_email='hanpama@gmail.com',
    url='https://github.com/hanpama/peppertext',
    packages=find_packages(),
    include_package_data=True,
    long_description=open('README.rst').read(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: Internet :: WWW/HTTP",
    ],
    install_requires=[
        "pyquery>=1.2.9",
        "requests>=2.8.1",
        "six",
    ],
    zip_safe=False,
)
