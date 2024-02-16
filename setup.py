import os.path
from setuptools import setup

# The directory containing this file
HERE = os.path.abspath(os.path.dirname(__file__))

# The text of the README file
with open(os.path.join(HERE, "README.md")) as fid:
    README = fid.read()

setup(
    name="orusexpert-visitor-allocator",
    version="1.0.0",
    description="Proyecto Asignador de visitas de Orusexpert",
    long_description=README,
    long_description_content_type="text/markdown",
    url="",
    author="Jeferson Rodriguez",
    author_email="jefferson.rc94@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    packages=["visitor_allocator"],
    include_package_data=True,
    install_requires=[
        "geopandas", "geopy", "haversine", "numpy", "pandas", "openpyxl",
        "scikit-learn", "scipy", "shapely", "utm", "matplotlib", "haversine",
    ],
    entry_points={"console_scripts": ["orusexpert=visitor_allocator.__main__:main"]},
)
