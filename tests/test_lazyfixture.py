# -*- coding: utf-8 -*-
import pytest
from pytest_lazyfixture import sorted_by_dependency, lazy_fixture, _sorted_argnames

try:
    import numpy
except ImportError:
    numpy = None


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
            pytest.param(1, pytest.lazy_fixture('zero'), marks=pytest.mark.xfail(reason=ZeroDivisionError))
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
            pytest.param(pytest.lazy_fixture('one'), marks=pytest.mark.skip(reason='skip'))
        ])
        def test_skip1(a):
            assert a == 1

        @pytest.mark.skip(reason='skip')
        @pytest.mark.parametrize('a', [
            pytest.lazy_fixture('one')
        ])
        def test_skip2(a):
            assert a == 1

        def test_after_skip(one):
            assert one == 1
    """)
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(skipped=2, passed=1)


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
                pytest.param(pytest.lazy_fixture('one'), marks=pytest.mark.skip(reason='skip this'))
            ])
            def test_model_b(self, a):
                assert a == 1

            def test_after_skip(self, one):
                assert one == 1
    """)
    reprec = testdir.runpytest('-s', '-v')
    reprec.assert_outcomes(skipped=2, passed=1)


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


def test_argnames_initialized_in_right_order(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture
        def one():
            return [1]

        @pytest.fixture
        def plus_two(a):
            a[0] = a[0] + 2

        @pytest.mark.parametrize('a,b', [
            (pytest.lazy_fixture('one'), pytest.lazy_fixture('plus_two'))
        ])
        def test_skip1(a, b):
            assert a == [3]
    """)
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(passed=1)


# https://github.com/TvoroG/pytest-lazy-fixture/pull/19
def test_argnames_initialized_in_right_order2(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture
        def one():
            return [1]

        @pytest.fixture
        def plus_two(a):
            a[0] = a[0] + 2
        def test_skip1(a):
            assert a == [3]

        def pytest_generate_tests(metafunc):
            metafunc.fixturenames = ['a', 'b']
            metafunc.parametrize(argnames=['a', 'b'],
                                 argvalues=[(pytest.lazy_fixture('one'), pytest.lazy_fixture('plus_two'))],
                                 indirect=['b'])

    """)
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(passed=1)


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
    sp = sorted_by_dependency(params, [])
    path = '>'.join(param for param, _ in sp)

    assert path in expected_paths


@pytest.mark.parametrize('params,fixturenames,expect_keys', [
    ({'b': 1, 'a': 0}, ['c', 'a', 'd', 'b'], ['c', 'a', 'd', 'b']),
    ({'b': 1, 'a': 0}, ['c', 'b'], ['c', 'b', 'a'])
])
def test_sorted_argnames(params, fixturenames, expect_keys):
    assert list(_sorted_argnames(params, fixturenames)) == expect_keys


def test_lazy_fixtures_with_subfixtures(testdir):
    testdir.makepyfile("""
        import pytest

        @pytest.fixture(params=["a", "A"])
        def a(request):
            return request.param

        @pytest.fixture(params=["b", "B"])
        def b(a, request):
            return request.param + a

        @pytest.fixture
        def c(a):
            return "c" + a

        @pytest.fixture(params=[pytest.lazy_fixture('a'), pytest.lazy_fixture('b'), pytest.lazy_fixture('c')])
        def d(request):
            return "d" + request.param

        @pytest.fixture(params=[pytest.lazy_fixture('a'), pytest.lazy_fixture('d'), ""])
        def e(request):
            return "e" + request.param

        def test_one(d):
            assert d in ("da", "dA", "dba", "dbA", "dBa", "dBA", "dca", "dcA")

        def test_two(e):
            assert e in ("ea", "eA", "eda", "edA", "edba", "edbA", "edBa", "edBA", "edca", "edcA", "e")
    """)
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(passed=19)


def test_lazy_fixtures_in_subfixture(testdir):
    testdir.makepyfile("""
        import pytest

        @pytest.fixture
        def a():
            return "a"

        @pytest.fixture
        def b():
            return "b"

        @pytest.fixture(params=[pytest.lazy_fixture('a'), pytest.lazy_fixture('b')])
        def c(request):
            return "c" + request.param

        @pytest.fixture
        def d(c):
            return "d" + c

        def test_one(d):
            assert d in ("dca", "dcb")
    """)
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(passed=2)


@pytest.mark.parametrize('autouse', [False, True])
def test_issues23(testdir, autouse):
    testdir.makepyfile("""
        import pytest

        @pytest.fixture(params=[0, 1], autouse={})
        def zero(request):
            return request.param

        @pytest.fixture(params=[1])
        def one(request, zero):
            return zero * request.param

        @pytest.fixture(params=[
            pytest.lazy_fixture('one'),
        ])
        def some(request):
            return request.param

        def test_func(some):
            assert some in [0, 1]

    """.format(autouse))
    reprec = testdir.inline_run('-s', '-v')
    reprec.assertoutcome(passed=2)


def test_lazy_fixture_nested_fixtures(testdir):
    testdir.makepyfile("""
        import pytest

        @pytest.fixture
        def one(request):
            return "SOME_VALUE"

        @pytest.fixture
        def two(request):
            return "SOME_VALUE2"

        @pytest.fixture(params=[
            pytest.lazy_fixture("one"),
            pytest.lazy_fixture("two"),
        ])
        def some_fixture1(request):
            return request.param

        @pytest.fixture
        def some_fixture2(some_fixture1):
            return "NEW_" + some_fixture1

        def test_func(some_fixture2):
            assert ((some_fixture2 == "NEW_SOME_VALUE") or (some_fixture2 == "NEW_SOME_VALUE2"))
    """)
    reprec = testdir.inline_run('-s')
    reprec.assertoutcome(passed=2)


# https://github.com/TvoroG/pytest-lazy-fixture/issues/39
def test_usefixture_runs_before_function_fixtures(testdir):
    testdir.makepyfile("""
        import pytest
        from pytest_lazyfixture import lazy_fixture

        invocation_order = []

        @pytest.fixture
        def module_fixture():
            invocation_order.append('using module fixture')

        @pytest.fixture
        def fixture1():
            invocation_order.append('using fixture1')
            return 'fixture1'

        @pytest.fixture
        def fixture2():
            invocation_order.append('using fixture2')
            return 'fixture2'

        @pytest.mark.usefixtures("module_fixture")
        @pytest.mark.parametrize("fixt", [lazy_fixture("fixture1"), lazy_fixture("fixture2")])
        def test_test(fixt):
            if fixt == 'fixture2':
                print(' '.join(invocation_order))
    """)
    result = testdir.runpytest('-s')
    stdout = result.stdout.str()
    assert (
        'using module fixture using fixture1 using module fixture using fixture2' in stdout
    )


# https://github.com/TvoroG/pytest-lazy-fixture/issues/39
def test_autouse_and_usefixture_module_scope_runs_before_function_fixtures(testdir):
    testdir.makepyfile("""
        import pytest
        from pytest_lazyfixture import lazy_fixture

        invocation_order = []

        @pytest.fixture(autouse=True)
        def autouse_fixture():
            invocation_order.append('using autouse_fixture')

        @pytest.fixture(scope='module')
        def module_fixture():
            invocation_order.append('using module fixture')

        @pytest.fixture
        def fixture1():
            invocation_order.append('using fixture1')
            return 'fixture1'

        @pytest.fixture
        def fixture2():
            invocation_order.append('using fixture2')
            return 'fixture2'

        @pytest.mark.usefixtures("module_fixture")
        @pytest.mark.parametrize("fixt", [lazy_fixture("fixture1"), lazy_fixture("fixture2")])
        def test_test(fixt):
            if fixt == 'fixture2':
                print(' '.join(invocation_order))
    """)
    result = testdir.runpytest('-s')
    stdout = result.stdout.str()
    assert (
        # pytest==3.2.5
        'using autouse_fixture using module fixture using fixture1 using autouse_fixture using fixture2' in stdout
        or
        'using module fixture using autouse_fixture using fixture1 using autouse_fixture using fixture2' in stdout
    )


@pytest.mark.parametrize('autouse_scope', [
    'session',
    'module',
    pytest.param('function', marks=pytest.mark.xfail)
])
def test_session_autouse_and_usefixture_module_scope_runs_before_function_fixtures(testdir, autouse_scope):
    testdir.makepyfile("""
        import pytest
        from pytest_lazyfixture import lazy_fixture

        invocation_order = []

        @pytest.fixture(autouse=True, scope='{autouse_scope}')
        def autouse_fixture():
            invocation_order.append('using autouse_fixture')

        @pytest.fixture(scope='module')
        def module_fixture():
            invocation_order.append('using module fixture')

        @pytest.fixture
        def fixture1():
            invocation_order.append("using fixture1")
            return 'fixture1'

        @pytest.fixture
        def fixture2():
            invocation_order.append("using fixture2")
            return 'fixture2'

        @pytest.mark.usefixtures("module_fixture")
        @pytest.mark.parametrize("fixt", [lazy_fixture("fixture1"), lazy_fixture("fixture2")])
        def test_test(fixt):
            if fixt == 'fixture2':
                print(' '.join(invocation_order))
    """.format(autouse_scope=autouse_scope))
    result = testdir.runpytest('-s')
    assert 'using autouse_fixture using module fixture using fixture1 using fixture2' in result.stdout.str()


# https://github.com/TvoroG/pytest-lazy-fixture/issues/39
def test_module_scope_runs_before_function_fixtures(testdir):
    testdir.makepyfile("""
        import pytest
        from pytest_lazyfixture import lazy_fixture

        invocation_order = []

        @pytest.fixture(scope='module')
        def module_fixture():
            invocation_order.append('using module fixture')

        @pytest.fixture
        def fixture1():
            invocation_order.append("using fixture1")
            return 'fixture1'

        @pytest.fixture
        def fixture2():
            invocation_order.append("using fixture2")
            return 'fixture2'

        @pytest.mark.parametrize("fixt", [lazy_fixture("fixture1"), lazy_fixture("fixture2")])
        def test_test(fixt, module_fixture):
            if fixt == 'fixture2':
                print(' '.join(invocation_order))
    """)
    result = testdir.runpytest('-s')
    stdout = result.stdout.str()
    assert (
        # pytest==3.2.5
        'using fixture1 using module fixture using fixture2' in stdout
        or
        'using module fixture using fixture1 using fixture2' in stdout
    )


# https://github.com/TvoroG/pytest-lazy-fixture/issues/42
@pytest.mark.skipif(numpy is None, reason='numpy is not installed')
def test_numpy_array_as_value(testdir):
    testdir.makepyfile("""
        import pytest
        import numpy as np

        @pytest.mark.parametrize(
            'value',
            [
                np.arange(10, dtype=np.int64),
                np.arange(10, dtype=np.int32),
            ]
        )
        def test_bug(value):
            assert isinstance(value, np.ndarray)
    """)
    result = testdir.inline_run('-s')
    result.assertoutcome(passed=2)
