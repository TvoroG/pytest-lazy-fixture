# -*- coding: utf-8 -*-
import pytest
from pytest_fixturemark import sorted_by_dependency


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

    def is_subset(subset, superset):
        return all(superset[k] == subset[k] for k in subset)
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


def test_fixture_mark_is_value_in_parametrize(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture
        def one():
            return 1
        @pytest.fixture
        def two():
            return 2
        @pytest.mark.parametrize('arg1,arg2', [
            pytest.mark.fixture(('one', 'two'))
        ])
        def test_func(arg1, arg2):
            assert arg1 == 1
            assert arg2 == 2
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=1)


def test_fixture_mark_as_funcarg_in_parametrize_with_indirect(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture
        def one():
            return 1
        @pytest.fixture
        def two():
            return 2
        @pytest.fixture
        def three(request):
            return request.param
        @pytest.mark.parametrize('arg1,arg2,three', [
            (pytest.mark.fixture('one'), pytest.mark.fixture('two'), '3')
        ], indirect=['three'])
        def test_func(arg1, arg2, three):
            assert arg1 == 1
            assert arg2 == 2
            assert three == '3'
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=1)


def test_fixture_mark_is_value_in_parametrize_with_indirect(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture
        def one(request):
            return request.param
        @pytest.fixture
        def two():
            return 2
        @pytest.mark.parametrize('one', [
            pytest.mark.fixture('two')
        ], indirect=True)
        def test_func(one):
            assert one == 2
    """)
    reprec = testdir.inline_run()
    reprec.assertoutcome(passed=1)


def test_fixture_mark_as_param_of_fixture(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture(params=[
            pytest.mark.fixture('one'),
            pytest.mark.fixture('two')
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
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=2)


def test_mark_fixture_in_params_which_has_params(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture(params=[1, 2, 3])
        def one(request):
            return str(request.param)
        @pytest.fixture
        def two():
            return 4
        @pytest.fixture(params=[
            pytest.mark.fixture('one'),
            pytest.mark.fixture('two')
        ])
        def some(request):
            return request.param
        def test_func(some):
            assert some in {'1', '2', '3', 4}
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=4)


def test_fixture_mark_three_times_nested(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture(params=[
            1, 2, pytest.mark.fixture('three')])
        def one(request):
            return str(request.param)
        @pytest.fixture
        def two():
            return 4
        @pytest.fixture
        def three():
            return 3
        @pytest.fixture(params=[
            pytest.mark.fixture('one'),
            pytest.mark.fixture('two')
        ])
        def some(request):
            return request.param
        def test_func(some):
            assert some in {'1', '2', '3', 4}
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=4)


def test_fixture_mark_three_times_nested_with_one_failed(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture(params=[
            1, 2, pytest.mark.fixture('three')
        ])
        def one(request):
            return str(request.param)
        @pytest.fixture
        def two():
            return 4
        @pytest.fixture
        def three():
            return 5
        @pytest.fixture(params=[
            pytest.mark.fixture('one'),
            pytest.mark.fixture('two')
        ])
        def some(request):
            return request.param
        def test_func(some):
            assert some in {'1', '2', '3', 4}
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=3, failed=1)


def fm(fname):
    return pytest.mark.fixture(fname)


@pytest.mark.parametrize('params,expected_paths', [
    (
        {'some': fm('one'), 'one': fm('three')},
        ['one>some'],
    ),
    (
        {'grand1': fm('parent1_1'), 'parent1_1': fm('child1'),
         'grand2': fm('parent1_2'), 'parent1_2': fm('child1'),
         'child1': fm('none')},
        ['child1>parent1_1>grand1>parent1_2>grand2', 'child1>parent1_2>grand2>parent1_1>grand1']
    ),
    (
        {'param1': 'val1', 'param2': 'val2'},
        ['param1>param2', 'param2>param1']
    ),
    ({}, ['']),
    ({'param1': 'val1'}, ['param1']),
    ({'param1': fm('some')}, ['param1'])
])
def test_sorted_by_dependency(params, expected_paths):
    sp = sorted_by_dependency(params)
    path = '>'.join(param for param, _ in sp)

    assert path in expected_paths
