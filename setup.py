#!/usr/bin/env python3
"""
Setup-Script für die Bibliothek-Empfehlungs-App
"""

from setuptools import setup, find_packages
import os

# Version aus version.py lesen
version_file = os.path.join(os.path.dirname(__file__), 'version.py')
version_data = {}
with open(version_file, 'r', encoding='utf-8') as f:
    exec(f.read(), version_data)

# README für PyPI
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Requirements
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='library-recommender',
    version=version_data['__version__'],
    author=version_data['__author__'],
    author_email='daniel.gaida@th-koeln.de',
    description=version_data['__description__'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dgaida/library-recommender',
    project_urls={
        'Bug Tracker': 'https://github.com/dgaida/library-recommender/issues',
        'Documentation': 'https://github.com/dgaida/library-recommender#readme',
        'Source Code': 'https://github.com/dgaida/library-recommender',
        'Changelog': 'https://github.com/dgaida/library-recommender/blob/main/CHANGELOG.md',
    },
    packages=find_packages(exclude=['tests', 'tests.*']),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Natural Language :: German',
    ],
    python_requires='>=3.8',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'library-recommender=main:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['*.md', '*.txt', '*.yaml', '*.yml'],
    },
    keywords='bibliothek library empfehlungen recommendations köln musik filme bücher',
    license=version_data['__license__'],
    zip_safe=False,
)