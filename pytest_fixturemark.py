# -*- coding: utf-8 -*-
import py
import os
import pytest
from _pytest.mark import MarkDecorator
from _pytest.fixtures import scopenum_function


def pytest_runtest_setup(item):
    if hasattr(item, 'callspec'):
        if has_fixture_mark(item) and not item.keywords['fixture'].args:
            for param, val in item.callspec.params.items():
                if not isinstance(val, MarkDecorator):
                    item.callspec.params[param] = MarkDecorator('fixture', args=(val,))

        for param, val in item.callspec.params.items():
            if isinstance(val, MarkDecorator) and val.name == 'fixture':
                fixture_name = val.args[0]
                item.callspec.params[param] = item._request.getfixturevalue(fixture_name)


def pytest_runtest_call(item):
    if hasattr(item, 'funcargs'):
        for arg, val in item.funcargs.items():
            if is_fixture_mark(val):
                item.funcargs[arg] = item._request.getfixturevalue(val.args[0])


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


def normalize_call(callspec, metafunc, valtype, used_keys=None):
    fm = metafunc.config.pluginmanager.get_plugin('funcmanage')
    config = metafunc.config

    used_keys = used_keys or set()
    # TODO: add some order (for example order of argnames in pytest.mark.parametrize)
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


def has_fixture_mark(item):
    return 'fixture' in item.keywords and is_fixture_mark(item.keywords['fixture'])


def is_fixture_mark(val):
    return isinstance(val, MarkDecorator) and val.name == 'fixture'


def get_nodeid(module, rootdir):
    path = py.path.local(module.__file__)
    relpath = path.relto(rootdir)
    if os.sep != "/":
        relpath = relpath.replace(os.sep, "/")
    return relpath
