from setuptools import setup, find_packages


version = '0.1.3b1'

requires = [
    # ft@ -- commented these out because I'm not sure we want
    # them as hard depencencies everywhere eduid-common is used
    #'pysaml2>=1.0.0',
    #'redis>=2.10.5',
]

test_requires = []

testing_extras = test_requires + []

long_description = open('README.txt').read()

setup(name='eduid-common',
      version=version,
      description="Common code for eduID applications",
      long_description=long_description,
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='NORDUnet A/S',
      author_email='',
      url='https://github.com/SUNET/',
      license='gpl',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['eduid_common'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      extras_require={
          'testing': testing_extras,
      },
      entry_points="""
      """,
      )
