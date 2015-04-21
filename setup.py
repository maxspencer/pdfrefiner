from distutils.core import setup
setup(
    name = 'pdfrefiner',
    packages = ['refiner', 'refiner.input', 'refiner.output'],
    version = '0.1',
    description = 'A python module for improving the output of PDF parsing and conversion tools.',
    author = 'Max Spencer',
    author_email = 'mrmaxspencer@gmail.com',
    url = 'https://github.com/maxspencer/pdfrefiner',
    download_url = 'https://github.com/maxspencer/pdfrefiner/archive/0.1.tar.gz',
    install_requires = [
        'beautifulsoup4',
    ],
    keywords = ['pdf', 'document'],
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.4'
    ],
)
