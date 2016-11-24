pytest-lazy-fixture |travis-ci| |appveyor| |pypi|
=================================================

Use your fixtures in ``@pytest.mark.parametrize``.

Installation
------------

.. code-block:: shell

    pip install pytest-lazy-fixture

Usage
-----

.. code-block:: python

    import pytest

    @pytest.fixture(params=[1, 2])
    def one(request):
        return request.param

    @pytest.mark.parametrize('arg1,arg2', [
        ('val1', pytest.lazy_fixture('one')),
    ])
    def test_func(arg1, arg2):
        assert arg2 in [1, 2]


Also you can use it as a parameter in ``@pytest.fixture``:

.. code-block:: python

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

Please see `tests <https://github.com/TvoroG/pytest-lazy-fixture/blob/master/tests/test_lazyfixture.py>`_ for more examples.

Contributing
------------

Contributions are very welcome. Tests can be run with ``tox``.

License
-------

Distributed under the terms of the ``MIT`` license,
``pytest-lazy-fixture`` is free and open source software

Issues
------

If you encounter any problems, please ``file an issue`` along with a
detailed description.

.. |travis-ci| image:: https://travis-ci.org/TvoroG/pytest-lazy-fixture.svg?branch=master
    :target: https://travis-ci.org/TvoroG/pytest-lazy-fixture
.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/TvoroG/pytest-fixture-mark?branch=master&svg=true
    :target: https://ci.appveyor.com/project/TvoroG/pytest-fixture-mark
.. |pypi| image:: https://badge.fury.io/py/pytest-lazy-fixture.svg
    :target: https://pypi.python.org/pypi/pytest-lazy-fixture/
