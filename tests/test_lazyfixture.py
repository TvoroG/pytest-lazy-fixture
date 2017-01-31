# -*- coding: utf-8 -*-
import pytest
from pytest_lazyfixture import sorted_by_dependency, lazy_fixture


def test_fixture_in_parametrize_with_params(testdir):
    items = testdir.getitems("""
        import pytest
        @pytest.fixture(params=[1,2])
        def one(request):
            return request.param
        @pytest.mark.parametrize('arg1,arg2', [
            ('val1', pytest.lazy_fixture('one')),
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
            ('val1', pytest.lazy_fixture('one'), pytest.lazy_fixture('two')),
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
            ('val1', pytest.lazy_fixture('two')),
        ], indirect=['one'])
        def test_func(arg1, one):
            pass
    """)
    assert len(items) == 1
    assert items[0].callspec.params['one'].name == 'two'


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
            ('val1', pytest.lazy_fixture('two')),
        ], indirect=['one'])
        def test_func(arg1, one):
            pass
    """)
    assert len(items) == 2
    assert items[0].callspec.params['two'] == 1
    assert items[1].callspec.params['two'] == 2


def test_lazy_fixture_is_value_in_parametrize(testdir):
    testdir.makepyfile("""
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
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=1)


def test_lazy_fixture_as_funcarg_in_parametrize_with_indirect(testdir):
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
            (pytest.lazy_fixture('one'), pytest.lazy_fixture('two'), '3')
        ], indirect=['three'])
        def test_func(arg1, arg2, three):
            assert arg1 == 1
            assert arg2 == 2
            assert three == '3'
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=1)


def test_lazy_fixture_is_value_in_parametrize_with_indirect(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture
        def one(request):
            return request.param
        @pytest.fixture
        def two():
            return 2
        @pytest.mark.parametrize('one', [
            pytest.lazy_fixture('two')
        ], indirect=True)
        def test_func(one):
            assert one == 2
    """)
    reprec = testdir.inline_run()
    reprec.assertoutcome(passed=1)


def test_lazy_fixture_as_param_of_fixture(testdir):
    testdir.makepyfile("""
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
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=2)


def test_lazy_fixture_in_params_which_has_params(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture(params=[1, 2, 3])
        def one(request):
            return str(request.param)
        @pytest.fixture
        def two():
            return 4
        @pytest.fixture(params=[
            pytest.lazy_fixture('one'),
            pytest.lazy_fixture('two')
        ])
        def some(request):
            return request.param
        def test_func(some):
            assert some in {'1', '2', '3', 4}
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=4)


def test_lazy_fixture_three_times_nested(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture(params=[
            1, 2, pytest.lazy_fixture('three')])
        def one(request):
            return str(request.param)
        @pytest.fixture
        def two():
            return 4
        @pytest.fixture
        def three():
            return 3
        @pytest.fixture(params=[
            pytest.lazy_fixture('one'),
            pytest.lazy_fixture('two')
        ])
        def some(request):
            return request.param
        def test_func(some):
            assert some in {'1', '2', '3', 4}
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=4)


def test_lazy_fixture_three_times_nested_with_one_failed(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture(params=[
            1, 2, pytest.lazy_fixture('three')
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
            pytest.lazy_fixture('one'),
            pytest.lazy_fixture('two')
        ])
        def some(request):
            return request.param
        def test_func(some):
            assert some in {'1', '2', '3', 4}
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=3, failed=1)


def test_lazy_fixture_common_dependency(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture(params=[1, 2, 3])
        def one(request):
            return request.param
        @pytest.fixture(params=[pytest.lazy_fixture('one')])
        def as_str(request):
            return str(request.param)
        @pytest.fixture(params=[pytest.lazy_fixture('one')])
        def as_hex(request):
            return hex(request.param)

        def test_as_str(as_str):
            assert as_str in {'1', '2', '3'}
        def test_as_hex(as_hex):
            assert as_hex in {'0x1', '0x2', '0x3'}

        def test_as_hex_vs_as_str(as_str, as_hex):
            assert int(as_hex, 16) == int(as_str)
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=9)


def test_lazy_fixture_common_dependency_with_getfixturevalue(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture(params=[1, 2, 3])
        def one(request):
            return request.param
        @pytest.fixture(params=[pytest.lazy_fixture('one')])
        def as_str(request):
            return str(request.getfixturevalue('one'))
        @pytest.fixture(params=[pytest.lazy_fixture('one')])
        def as_hex(request):
            return hex(request.getfixturevalue('one'))
        def test_as_str(as_str):
            assert as_str in {'1', '2', '3'}
        def test_as_hex(as_hex):
            assert as_hex in {'0x1', '0x2', '0x3'}
        def test_as_hex_vs_as_str(as_str, as_hex):
            assert int(as_hex, 16) == int(as_str)
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=9)


def test_issues2(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture(params=[1, 2, 3])
        def one(request):
            return request.param

        @pytest.fixture(params=[pytest.lazy_fixture('one')])
        def as_str(request):
            return str(request.getfixturevalue('one'))

        @pytest.mark.parametrize('val', ('a', 'b', 'c'))
        def test_as_str(val, as_str):
            combined = ''.join((val, as_str))
            assert combined in {'a1', 'a2', 'a3', 'b1', 'b2', 'b3', 'c1', 'c2', 'c3'}
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=9)


def test_issues2_2(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture(params=[1, 2, 3])
        def one(request):
            return request.param

        @pytest.fixture(params=[pytest.lazy_fixture('one')])
        def as_str(request):
            return str(request.getfixturevalue('one'))

        @pytest.mark.parametrize('val, one', (
            ('a', '1'), ('b', '2'), ('c', '3')
        ), indirect=['one'])
        def test_as_str(val, one, as_str):
            combined = ''.join((val, as_str))
            assert combined in {'a1', 'b2', 'c3'}
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=3)


def test_issues3_autouse_fixtures_should_run_first(testdir):
    testdir.makepyfile("""
        import pytest
        gl = False
        @pytest.fixture(autouse=True)
        def auto_one():
            global gl
            gl = True

        @pytest.fixture
        def one():
            return 1 if gl is True else -1

        @pytest.mark.parametrize('arg1', [
            pytest.lazy_fixture('one')
        ])
        def test_some(arg1):
            assert arg1 == 1
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=1)


def test_issues10_xfail(testdir):
    testdir.makepyfile("""
        import pytest
        def division(a, b):
            return a / b

        @pytest.fixture(params=[0])
        def zero(request):
            return request.param

        @pytest.mark.parametrize(('a', 'b'), [
            pytest.mark.xfail((1, pytest.lazy_fixture('zero')), reason=ZeroDivisionError)
        ])
        def test_division(a, b):
            division(a, b)
    """)
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(skipped=1)


def test_issues11_autouse_fixture_in_test_class(testdir):
    testdir.makepyfile("""
        import pytest

        class TestModels(object):
            @pytest.fixture(autouse=True)
            def setup(self):
                self.var = 15

            def test_model_a(self):
                assert self.var == 15

            def test_model_b(self):
                assert self.var == 15

    """)
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(passed=2)


def test_issues12_skip_test_function(testdir):
    testdir.makepyfile("""
        import pytest

        @pytest.fixture
        def one():
            return 1

        @pytest.mark.parametrize('a', [
            pytest.mark.skip((pytest.lazy_fixture('one'),), reason='skip')
        ])
        def test_skip1(a):
            assert a == 1

        @pytest.mark.skip(reason='skip')
        @pytest.mark.parametrize('a', [
            pytest.lazy_fixture('one')
        ])
        def test_skip2(a):
            assert a == 1
    """)
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(skipped=2)


def test_issues12_skip_test_method(testdir):
    testdir.makepyfile("""
        import pytest

        class TestModels:
            @pytest.fixture
            def one(self):
                return 1

            @pytest.mark.skip(reason='skip this')
            @pytest.mark.parametrize('a', [
                pytest.lazy_fixture('one')
            ])
            def test_model_a(self, a):
                assert a == 1

            @pytest.mark.parametrize('a', [
                pytest.mark.skip((pytest.lazy_fixture('one'),), reason='skip this')
            ])
            def test_model_b(self, a):
                assert a == 1
    """)
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(skipped=2)


def test_issues12_lf_as_method_of_test_class(testdir):
    testdir.makepyfile("""
        import pytest

        class TestModels:
            @pytest.fixture
            def one(self):
                return 1

            @pytest.mark.parametrize('a', [
                pytest.lazy_fixture('one')
            ])
            def test_lf(self, a):
                assert a == 1
    """)
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(passed=1)


def test_issues13_unittest_testcase_class_should_not_fail(testdir):
    testdir.makepyfile("""
        import unittest
        import pytest

        class TestModels(unittest.TestCase):
            def test_models(self):
                assert True

            def test_models_fail(self):
                assert False
    """)
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(passed=1, failed=1)


def lf(fname):
    return lazy_fixture(fname)


@pytest.mark.parametrize('params,expected_paths', [
    (
        {'some': lf('one'), 'one': lf('three')},
        ['one>some'],
    ),
    (
        {'grand1': lf('parent1_1'), 'parent1_1': lf('child1'),
         'grand2': lf('parent1_2'), 'parent1_2': lf('child1'),
         'child1': lf('none')},
        ['child1>parent1_1>grand1>parent1_2>grand2', 'child1>parent1_2>grand2>parent1_1>grand1']
    ),
    (
        {'param1': 'val1', 'param2': 'val2'},
        ['param1>param2', 'param2>param1']
    ),
    ({}, ['']),
    ({'param1': 'val1'}, ['param1']),
    ({'param1': lf('some')}, ['param1']),
    (
        {'one': 1, 'as_str': lf('one'), 'as_hex': lf('one')},
        ['one>as_str>as_hex', 'one>as_hex>as_str']
    )
])
def test_sorted_by_dependency(params, expected_paths):
    sp = sorted_by_dependency(params)
    path = '>'.join(param for param, _ in sp)

    assert path in expected_paths
