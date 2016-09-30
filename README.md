pytest-fixture-mark
===================================

It helps to use fixtures in pytest.mark.parametrize ([issues/349](https://github.com/pytest-dev/pytest/issues/349))

Not ready yet


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
Contributions are very welcome. Tests can be run with `tox`, please ensure
the coverage at least stays the same before you submit a pull request.

License
-------

Distributed under the terms of the `MIT` license, "pytest-fixture-mark" is free and open source software


Issues
------

If you encounter any problems, please `file an issue` along with a detailed description.
