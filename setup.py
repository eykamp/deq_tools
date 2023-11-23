# https://github.com/fhamborg/news-please/wiki/PyPI---How-to-upload-a-new-version
# Create new release on GitHub (tag commit with v0.2.3)
# update this file with new version and download_url
# Run the following:
#    python setup.py sdist
#    twine check dist/*
# check SOURCES.txt to make sure no extraneous files were included
#    twine upload dist/*
#    del deq_tools.egg-info
#    del dist
#    del build   rem does this really exist?

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
	name="deq_tools",
    version="0.3.0",
    download_url="https://github.com/eykamp/deq_tools/archive/v0.3.0.tar.gz",
    author="Chris Eykamp",
    author_email="chris@eykamp.com",
    description="Tools for downloading Oregon DEQ Air Quality data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eykamp/deq_tools",
    packages=setuptools.find_packages(),
    license="MIT",
    keywords=["deq","airquality","data"],
    classifiers=[
      	"Programming Language :: Python :: 3",
      	"License :: OSI Approved :: MIT License",
      	"Operating System :: OS Independent",
    ],
    install_requires=[
        "requests",
        "pydantic",
        "tenacity",
    ],
)
