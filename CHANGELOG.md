# django-relativity changelog

## [Unreleased]
- Allowed for callable predicates (thanks django-reverse-unique)
- Fix bug in get_forward_related_filter() causing unnecessarily complicated queries
- Fix bug when building exclude filters

## 0.1.3 - 2018-08-31
- Added descendant and subtree fields for django-treebeard
- Added subtree field for django-mptt
- Modified some tests to use subtree fields 
- Added a changelog
- Added Django 2.1 to test matrix
