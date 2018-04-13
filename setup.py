import os
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='django-relationships',
    version='0.1a1',
    description='An endlessly flexible relationship field for your Django models.',
    license='BSD',
    long_description='',
    url='https://github.com/alexhill/django-keyparty',
    author='Alex Hill',
    author_email='alex@hill.net.au',

    packages=find_packages(),
    install_requires=['django<2.0'],

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
