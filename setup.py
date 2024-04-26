#!/usr/bin/env python
from __future__ import print_function

import os
import sys
from setuptools import setup


if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    os.system("python setup.py bdist_wheel upload")
    print("You probably want to also tag the version now:")
    print("  git tag -a VERSION -m 'version VERSION'")
    print("  git push --tags")
    sys.exit()

setup(
    name="noteshrink-dark",
    version="0.2.1",
    author="Matt Zucker",
    maintainer="Siddhant Laddha",
    description="Convert scans of handwritten notes to beautiful, compact PDFs with Dark Mode!",
    url="https://github.com/siddhantladdha/noteshrink-dark",
    py_modules=["noteshrink-dark", "pdf_eat_pdf_shit"],
    install_requires=[
        "numpy>=1.1.0",
        "scipy",
        "pillow",
    ],
    entry_points="""
        [console_scripts]
        noteshrink-dark=noteshrink:main
        pdf-eat-pdf-shit=pdf_eat_pdf_shit:main
    """,
)
