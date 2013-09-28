import os
from setuptools import setup

setup(name="HWFormatter",
      author="David Robinson",
      author_email="dgrtwo@princeton.edu",
      url="http://github.com/dgrtwo/HW-Formatter",
      description="Format submitted homework assignments from Blackboard " +
                    "into PDFs",
      packages=["HWFormatter"],
      package_dir={"HWFormatter": os.path.join("src", "HWFormatter")},
      install_requires=["pyPdf"],
      version="0.4",
      scripts=[os.path.join("scripts", "format_HW")],
      )
