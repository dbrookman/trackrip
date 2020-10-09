import pathlib
from setuptools import setup
from trackrip import __version__

here = pathlib.Path(__file__).parent.resolve()
README = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name = "trackrip",
    version = __version__,
    description = "Extracts samples from various music tracker module formats",
    long_description = README,
    long_description_content_type = "text/markdown",
    url = "https://github.com/dbrookman/trackrip",
    author = "Daniel Brookman",
    author_email = "dannntrax@gmail.com",
    license = "MIT",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Conversion"
    ],
    keywords = "tracker music samples mod s3m it",
    packages = ["trackrip"],
    python_requires = ">=3.7",
    entry_points={
        'console_scripts': [
            'trackrip=trackrip.__main__:main',
        ],
    },
)