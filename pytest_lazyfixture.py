# -*- coding: utf-8 -*-
import sys
import types
from collections import defaultdict
import pytest
from _pytest.fixtures import scopenum_function


PY3 = sys.version_info[0] == 3
string_type = str if PY3 else basestring


def pytest_configure():
    pytest.lazy_fixture = lazy_fixture


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    if hasattr(item, '_request'):
        item._request._fillfixtures = types.MethodType(
            fillfixtures(item._request._fillfixtures), item._request
        )


def fillfixtures(_fillfixtures):
    def fill(request):
        item = request._pyfuncitem
        fixturenames = item.fixturenames
        argnames = item._fixtureinfo.argnames

        for fname in fixturenames:
            if fname not in item.funcargs and fname not in argnames:
                item.funcargs[fname] = request.getfixturevalue(fname)

        if hasattr(item, 'callspec'):
            for param, val in sorted_by_dependency(item.callspec.params, fixturenames):
                if is_lazy_fixture(val):
                    item.callspec.params[param] = request.getfixturevalue(val.name)

        _fillfixtures()
    return fill


def pytest_runtest_call(item):
    if hasattr(item, 'funcargs'):
        for arg, val in item.funcargs.items():
            if is_lazy_fixture(val):
                item.funcargs[arg] = item._request.getfixturevalue(val.name)


@pytest.hookimpl(hookwrapper=True)
def pytest_pycollect_makeitem(collector, name, obj):
    global current_node
    current_node = collector
    yield
    current_node = None


@pytest.hookimpl(hookwrapper=True)
def pytest_generate_tests(metafunc):
    yield

    normalize_metafunc_calls(metafunc, 'funcargs')
    normalize_metafunc_calls(metafunc, 'params')


def normalize_metafunc_calls(metafunc, valtype):
    newcalls = []
    for callspec in metafunc._calls:
        calls = normalize_call(callspec, metafunc, valtype)
        newcalls.extend(calls)
    metafunc._calls = newcalls


def parametrize_callspecs(callspecs, metafunc, fname, fparams):
    allnewcallspecs = []
    for i, param in enumerate(fparams):
        try:
            newcallspecs = [call.copy() for call in callspecs]
        except TypeError:
            # pytest < 3.6.3
            newcallspecs = [call.copy(metafunc) for call in callspecs]

        # TODO: for now it uses only function scope
        # TODO: idlist
        setmulti_args = (
            {fname: 'params'}, (fname,), (param,),
            None, (), scopenum_function, i
        )
        try:
            for newcallspec in newcallspecs:
                newcallspec.setmulti2(*setmulti_args)
        except AttributeError:
            # pytest < 3.3.0
            for newcallspec in newcallspecs:
                newcallspec.setmulti(*setmulti_args)
        allnewcallspecs.extend(newcallspecs)
    return allnewcallspecs


def normalize_call(callspec, metafunc, valtype, used_keys=None):
    fm = metafunc.config.pluginmanager.get_plugin('funcmanage')

    used_keys = used_keys or set()
    valtype_keys = set(getattr(callspec, valtype).keys()) - used_keys

    for arg in valtype_keys:
        val = getattr(callspec, valtype)[arg]
        if is_lazy_fixture(val):
            try:
                _, fixturenames_closure, arg2fixturedefs = fm.getfixtureclosure([val.name], metafunc.definition.parent)
            except AttributeError:
                # pytest < 3.10.0
                fixturenames_closure, arg2fixturedefs = fm.getfixtureclosure([val.name], current_node)

            extra_fixture_params = [(fname, arg2fixturedefs[fname][-1].params)
                                    for fname in fixturenames_closure if fname not in callspec.params
                                    if arg2fixturedefs.get(fname) and arg2fixturedefs[fname][-1].params]

            if extra_fixture_params:
                newcallspecs = [callspec]
                for fname, fparams in extra_fixture_params:
                    newcallspecs = parametrize_callspecs(newcallspecs, metafunc, fname, fparams)
                newcalls = []
                for newcallspec in newcallspecs:
                    calls = normalize_call(newcallspec, metafunc, valtype, used_keys | set([arg]))
                    newcalls.extend(calls)
                return newcalls
        used_keys = used_keys | set([arg])
    return [callspec]


def sorted_by_dependency(params, fixturenames):
    free_fm = []
    non_free_fm = defaultdict(list)

    for key in _sorted_argnames(params, fixturenames):
        val = params[key]

        if not is_lazy_fixture(val) or val.name not in params:
            free_fm.append(key)
        else:
            non_free_fm[val.name].append(key)

    non_free_fm_list = []
    for free_key in free_fm:
        non_free_fm_list.extend(
            _tree_to_list(non_free_fm, free_key)
        )

    return [(key, params[key]) for key in (free_fm + non_free_fm_list)]


def _sorted_argnames(params, fixturenames):
    argnames = set(params.keys())

    for name in fixturenames:
        if name in argnames:
            argnames.remove(name)
            yield name

    if argnames:
        for name in argnames:
            yield name


def _tree_to_list(trees, leave):
    lst = []
    for l in trees[leave]:
        lst.append(l)
        lst.extend(
            _tree_to_list(trees, l)
        )
    return lst


def lazy_fixture(names):
    if isinstance(names, string_type):
        return LazyFixture(names)
    else:
        return [LazyFixture(name) for name in names]


def is_lazy_fixture(val):
    return isinstance(val, LazyFixture)


class LazyFixture(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return self.name == other.name
