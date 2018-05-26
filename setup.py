# https://github.com/fhamborg/news-please/wiki/PyPI---How-to-upload-a-new-version
# Create new release on GitHub
# update this file with new version and download_url
# Run the following:
#    python setup.py sdist
#    python -m twine upload dist/*

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    download_url='https://github.com/eykamp/deq_tools/archive/v0.1.2.tar.gz',
    version='0.1.2',
	name='deq_tools',
    author='Chris Eykamp',
    author_email='chris@eykamp.com',
    description='Tools for downloading Oregon DEQ Air Quality data',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/eykamp/deq_tools',
    packages=setuptools.find_packages(),
    license='MIT',
    keywords=['deq','airquality','data'],
    classifiers=[
      	"Programming Language :: Python :: 3",
      	"License :: OSI Approved :: MIT License",
      	"Operating System :: OS Independent",
    ],
)
