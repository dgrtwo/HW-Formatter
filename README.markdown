HWFormatter
============

HWFormatter is a simple Python script that lets instructors format assignment files downloaded from Blackboard into individual per-student PDFs. This makes it easier to grade and return them. This is especially useful for assignments that include one or more code files, since it performs syntax highlighting before combining them into the PDF.

This software is at a very early stage of development: suggestions or contributions are *strongly* encouraged!

Installation
------------

You can install HWFormatter from the [Python Package Index](http://pypi.python.org/pypi) using:

    easy_install HWFormatter

or using pip:

    pip install HWFormatter

(On Linux or Macs, you might need to add `sudo` to the start of each command). You can also install it from source:

    python setup.py build
    python setup.py install

Usage
-----

Download the submitted assignment files from Blackboard:

 * Go to Course Management->Grade Center->Assignments
 * Select the arrow at the top of the column of assignments you're interested in downloading. 
 * Click "Assignment File Download"- it will download as a .zip file.
 * Unzip the downloaded file.
 
Then run:

    format_HW infolder outfolder

The output folder will then contain one PDF file per student ID.