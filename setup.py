import sys
from setuptools import setup


if sys.version_info.major != 3:
    print("This Python is only compatible with Python 3, but you are running "
          "Python {}. The installation will likely fail.".format(sys.version_info.major))

setup(name='raic2018',
    install_requires=[],
    description="RAIC 2018 CodeBall",
    author="Alexander Penkin",
    author_email="sss13594@gmail.com",
    version="0.1",
    packages=['raic2018'],
    zip_safe=False)
