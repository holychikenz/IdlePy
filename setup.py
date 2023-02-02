import os
from setuptools import setup, Extension

VERSION = "0.0.2"

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

extensions = [
    Extension(
        "fishing",
        ["idlescape_cpp/fishing.cpp"]
    )
]

setup(
    name = "idlescape",
    version = VERSION,
    packages=['idlescape', 'idlescape.dashboard'],
    package_data={"idlescape": ["data/*"]},
    #ext_package="idlescape_cpp",
    #ext_modules=extensions,
)
