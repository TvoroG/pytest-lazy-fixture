# -*- coding: utf-8 -*-
import py
import os
from collections import defaultdict
import pytest
from _pytest.mark import MarkDecorator
from _pytest.fixtures import scopenum_function


def pytest_runtest_setup(item):
    if hasattr(item, 'callspec'):
        for param, val in sorted_by_dependency(item.callspec.params):
            if is_fixture_mark(val):
                item.callspec.params[param] = item._request.getfixturevalue(fixture_name(val))


def pytest_runtest_call(item):
    if hasattr(item, 'funcargs'):
        for arg, val in item.funcargs.items():
            if is_fixture_mark(val):
                item.funcargs[arg] = item._request.getfixturevalue(val.args[0])


@pytest.hookimpl(hookwrapper=True)
def pytest_generate_tests(metafunc):
    yield

    for callspec in metafunc._calls:
        if has_fixture_mark(callspec.keywords) and not callspec.keywords['fixture'].args:
            callspec.funcargs = all_as_fixture(callspec.funcargs)
            callspec.params = all_as_fixture(callspec.params)

    normalize_metafunc_calls(metafunc, 'funcargs')
    normalize_metafunc_calls(metafunc, 'params')


def normalize_metafunc_calls(metafunc, valtype):
    newcalls = []
    for callspec in metafunc._calls:
        calls = normalize_call(callspec, metafunc, valtype)
        newcalls.extend(calls)
    metafunc._calls = newcalls


def normalize_call(callspec, metafunc, valtype, used_keys=None):
    fm = metafunc.config.pluginmanager.get_plugin('funcmanage')
    config = metafunc.config

    used_keys = used_keys or set()
    valtype_keys = set(getattr(callspec, valtype).keys()) - used_keys

    newcalls = []
    for arg in valtype_keys:
        val = getattr(callspec, valtype)[arg]
        if is_fixture_mark(val):
            fname = val.args[0]
            nodeid = get_nodeid(metafunc.module, config.rootdir)
            fdef = fm.getfixturedefs(fname, nodeid)
            if fdef and fdef[-1].params:
                for i, param in enumerate(fdef[0].params):
                    newcallspec = callspec.copy(metafunc)
                    # TODO: for now it uses only function scope
                    # TODO: idlist
                    newcallspec.setmulti({fname: 'params'},
                                         (fname,), (param,),
                                         None, (), scopenum_function, i)
                    calls = normalize_call(newcallspec, metafunc, valtype, used_keys | set([arg]))
                    newcalls.extend(calls)
                return newcalls
        used_keys = used_keys | set([arg])
    return [callspec]


def all_as_fixture(d):
    return {key: val if is_fixture_mark(val) else pytest.mark.fixture(val) for key, val in d.items()}


def sorted_by_dependency(params):
    not_fm = []
    free_fm = []
    non_free_fm = defaultdict(list)

    for key in params:
        val = params[key]

        if not is_fixture_mark(val):
            not_fm.append(key)
        elif fixture_name(val) not in params:
            free_fm.append(key)
        else:
            non_free_fm[fixture_name(val)].append(key)

    non_free_fm_list = []
    for free_key in free_fm:
        non_free_fm_list.extend(
            _tree_to_list(non_free_fm, free_key)
        )

    return [(key, params[key]) for key in (not_fm + free_fm + non_free_fm_list)]


def _tree_to_list(trees, leave):
    lst = []
    for l in trees[leave]:
        lst.append(l)
        lst.extend(
            _tree_to_list(trees, l)
        )
    return lst


def has_fixture_mark(keywords):
    return 'fixture' in keywords and is_fixture_mark(keywords['fixture'])


def is_fixture_mark(val):
    return isinstance(val, MarkDecorator) and val.name == 'fixture'


def fixture_name(fixture_mark):
    return fixture_mark.args[0]


def get_nodeid(module, rootdir):
    path = py.path.local(module.__file__)
    relpath = path.relto(rootdir)
    if os.sep != "/":
        relpath = relpath.replace(os.sep, "/")
    return relpath
