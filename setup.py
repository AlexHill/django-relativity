import os
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='django-relativity',
    version='0.1a1',
    description='A flexible relationship field for the Django ORM.',
    license='BSD',
    long_description='',
    long_description_content_type='text/markdown',
    url='https://github.com/alexhill/django-relativity',
    author='Alex Hill',
    author_email='alex@hill.net.au',

    packages=find_packages(),
    install_requires=['django>=1.11'],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python',
    ],
)
