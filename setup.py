import os
from setuptools import setup

VERSION = "0.0.2"

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
        name = "idlescape",
        version = VERSION,
        packages=['idlescape', 'idlescape.dashboard'],
        package_data={"idlescape": ["data/*"]},
)
