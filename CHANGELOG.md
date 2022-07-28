# django-relativity changelog

## 0.2.6 - 2022-07-28
- Added support for Django 4 (thanks to AlexCLeduc)

## 0.2.5 - 2021-10-06
- Fixed a crash when accessing a single related descriptor on a Relationship whose predicate contains a bare primitive value, i.e. not wrapped in `Value()`.

## 0.2.4 - 2021-04-29
- Until Django's behaviour can be emulated, don't cache related objects

## 0.2.3 - 2021-04-28
- Improved behaviour of Relationship fields with null=True
- Allowed using L() inside complex expressions in predicate

## 0.2.2 - 2020-05-30
- Fixed crash when reverse_multiple=False

## 0.2.1 - 2020-02-10
- Restored Q and F from relativity.compat as aliases to django.db.models, with a deprecation warning on import
- Added monkeypatch for migrations where a model with a Relationship is the target of a ForeignKey

## 0.2.0 - 2020-02-08
- Relationship now works without generating migrations
- Removed all old compat code
- Added testing again Django master

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
