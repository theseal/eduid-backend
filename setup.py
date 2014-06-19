import os

from setuptools import setup, find_packages

__author__ = 'leifj'

here = os.path.abspath(os.path.dirname(__file__))
README_fn = os.path.join(here, 'README.rst')
README = 'eduID Message Manager'
if os.path.exists(README_fn):
    README = open(README_fn).read()

version = '0.7.12-dev'

install_requires = [
    'eduid_am>=0.4.8-dev',
    'python-dateutil == 2.1',
    'pymongo == 2.6.3',
    'celery == 3.1.9',
    'pysmscom == 0.4',
    'pymmclient == 0.7.2',
    'pynavet == 0.6.0',
    'Jinja2 == 2.7.3',
]

testing_extras = [
    'nose==1.2.1',
    'nosexcover==1.0.8',
    'coverage==3.6',
    'mock==1.0.1',
    'jinja2',
]

setup(
    name='eduid_msg',
    version=version,
    description="eduID Message Manager",
    long_description=README,
    classifiers=[
        # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords='identity federation saml',
    author='Leif Johansson',
    author_email='leifj@sunet.se',
    url='http://blogs.mnt.se',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    package_data = {
        },
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'testing': testing_extras,
    },
    test_suite='eduid_msg',
)
