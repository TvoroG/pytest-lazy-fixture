# -*- coding: utf-8 -*-


def test_fixture_in_parametrize_with_params(testdir):
    items = testdir.getitems("""
        import pytest
        @pytest.fixture(params=[1,2])
        def one(request):
            return request.param
        @pytest.mark.parametrize('arg1,arg2', [
            ('val1', pytest.mark.fixture('one')),
            ('val1', 'val2')
        ])
        def test_func(arg1, arg2):
            pass
    """)
    assert len(items) == 3
    assert items[0].callspec.params['one'] == 1
    assert items[1].callspec.params['one'] == 2


def test_several_fixtures_in_parametrize_with_params(testdir):
    items = testdir.getitems("""
        import pytest
        @pytest.fixture(params=[1,2])
        def one(request):
            return request.param
        @pytest.fixture(params=[3,4])
        def two(request):
            return request.param
        @pytest.mark.parametrize('arg1,arg2,arg3', [
            ('val1', pytest.mark.fixture('one'), pytest.mark.fixture('two')),
        ])
        def test_func(arg1, arg2, arg3):
            pass
    """)
    assert len(items) == 4
    expected_results = [
        {'one': 1, 'two': 3},
        {'one': 1, 'two': 4},
        {'one': 2, 'two': 3},
        {'one': 2, 'two': 4}
    ]

    is_subset = lambda subset, superset: all(superset[k] == subset[k] for k in subset)
    for item in items:
        assert any(is_subset(result, item.callspec.params) for result in expected_results)


def test_fixtures_in_parametrize_with_indirect(testdir):
    items = testdir.getitems("""
        import pytest
        @pytest.fixture
        def one():
            pass
        @pytest.fixture
        def two():
            pass
        @pytest.mark.parametrize('arg1,one', [
            ('val1', pytest.mark.fixture('two')),
        ], indirect=['one'])
        def test_func(arg1, one):
            pass
    """)
    assert len(items) == 1
    assert items[0].callspec.params['one'].name == 'fixture'
    assert items[0].callspec.params['one'].args == ('two',)


def test_fixtures_with_params_in_parametrize_with_indirect(testdir):
    items = testdir.getitems("""
        import pytest
        @pytest.fixture
        def one():
            pass
        @pytest.fixture(params=[1,2])
        def two(request):
            return request.param
        @pytest.mark.parametrize('arg1,one', [
            ('val1', pytest.mark.fixture('two')),
        ], indirect=['one'])
        def test_func(arg1, one):
            pass
    """)
    assert len(items) == 2
    assert items[0].callspec.params['two'] == 1
    assert items[1].callspec.params['two'] == 2
