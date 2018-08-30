import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    author='Alex Hill',
    author_email='alex@hill.net.au',
    name='django-relativity',
    version='0.1.3',
    description='A flexible relationship field for the Django ORM.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alexhill/django-relativity',
    packages=setuptools.find_packages(),
    install_requires=['django>=1.11'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
)
