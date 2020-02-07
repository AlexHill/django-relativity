# django-relativity changelog

## 0.1.5 - 2020-02-07
- Fixed and added testing against PostgreSQL and MySQL/MariaDB
- Added support for Django 2.2 and 3.0

## 0.1.4 - 2018-09-14
- Allowed for callable predicates (thanks django-reverse-unique)
- Fix bug in get_forward_related_filter() causing unnecessarily complicated queries
- Fix bug when building exclude filters
- Fix migrations under Django <2.0

## 0.1.3 - 2018-08-31
- Added descendant and subtree fields for django-treebeard
- Added subtree field for django-mptt
- Modified some tests to use subtree fields 
- Added a changelog
- Added Django 2.1 to test matrix
