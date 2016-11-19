pytest-lazy-fixture ![build status](https://travis-ci.org/TvoroG/pytest-lazy-fixture.svg?branch=master) ![build status](https://ci.appveyor.com/api/projects/status/github/TvoroG/pytest-fixture-mark?branch=master&svg=true)
===================================

It helps to use fixtures in pytest.mark.parametrize.

Usage
-----

```python
import pytest

@pytest.fixture(params=[1, 2])
def one(request):
    return request.param

@pytest.mark.parametrize('arg1,arg2', [
    ('val1', pytest.lazy_fixture('one')),
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
    ('val1', pytest.lazy_fixture('two')),
], indirect=['one'])
def test_func(arg1, one):
    assert one in [3, 4]
```

``` python
import pytest

@pytest.fixture
def one():
    return 1

@pytest.fixture
def two():
    return 2

@pytest.mark.parametrize('arg1,arg2', [
    pytest.lazy_fixture(('one', 'two'))
])
def test_func(arg1, arg2):
    assert arg1 == 1
    assert arg2 == 2
```

``` python
import pytest

@pytest.fixture(params=[
    pytest.lazy_fixture('one'),
    pytest.lazy_fixture('two')
])
def some(request):
    return request.param

@pytest.fixture
def one():
    return 1

@pytest.fixture
def two():
    return 2

def test_func(some):
    assert some in [1, 2]
```

Contributing
------------
Contributions are very welcome. Tests can be run with `tox`.

License
-------

Distributed under the terms of the `MIT` license, "pytest-lazy-fixture" is free and open source software


Issues
------

If you encounter any problems, please `file an issue` along with a detailed description.
