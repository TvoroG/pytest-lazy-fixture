pytest-fixture-mark
===================================

.. image:: https://travis-ci.org/tvorog/pytest-fixture-mark.svg?branch=master
    :target: https://travis-ci.org/tvorog/pytest-fixture-mark
    :alt: See Build Status on Travis CI

.. image:: https://ci.appveyor.com/api/projects/status/github/tvorog/pytest-fixture-mark?branch=master
    :target: https://ci.appveyor.com/project/tvorog/pytest-fixture-mark/branch/master
    :alt: See Build Status on AppVeyor

It helps to use fixtures in pytest.mark.parametrize ([issues/349](https://github.com/pytest-dev/pytest/issues/349))

Not ready yet
----


Usage
-----

```python
import pytest

@pytest.fixture(params=[1, 2])
def one(request):
    return request.param

@pytest.mark.parametrize('arg1,arg2', [
    ('val1', pytest.mark.fixture('one')),
])
def test_func(arg1, arg2):
    assert arg2 in [1, 2]
```

```python
import pytest

@pytest.fixture
def one(request):
    return request.param + 2

@pytest.fixture(params=[1,2])
def two(request):
    return request.param

@pytest.mark.parametrize('arg1,one', [
    ('val1', pytest.mark.fixture('two')),
], indirect=['one'])
def test_func(arg1, one):
    assert one in [3, 4]
```

Features
--------

* TODO

Contributing
------------
Contributions are very welcome. Tests can be run with `tox`_, please ensure
the coverage at least stays the same before you submit a pull request.

License
-------

Distributed under the terms of the `MIT`_ license, "pytest-fixture-mark" is free and open source software


Issues
------

If you encounter any problems, please `file an issue`_ along with a detailed description.
