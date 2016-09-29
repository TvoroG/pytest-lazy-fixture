# -*- coding: utf-8 -*-
import py
import os
import pytest
from _pytest.mark import MarkDecorator, MarkInfo
from _pytest.fixtures import getfixturemarker, FixtureDef, scopenum_function


def pytest_runtest_setup(item):
    # if 'fixture' in item.keywords and isinstance(item.keywords['fixture'], MarkInfo):
    #     for mark in item.keywords['fixture']:
    #         fixture_name = mark.args[0]
    #         item.funcargs[fixture_name] = item._request.getfixturevalue(fixture_name)

    if hasattr(item, 'callspec'):
        for param in item.callspec.params:
            val = item.callspec.params[param]
            if isinstance(val, MarkDecorator) and val.name == 'fixture':
                fixture_name = val.args[0]
                item.callspec.params[param] = item._request.getfixturevalue(fixture_name)


def pytest_runtest_call(item):
    for arg in item.funcargs:
        val = item.funcargs[arg]
        if isinstance(val, MarkDecorator) and val.name == 'fixture':
            fixture_name = val.args[0]
            item.funcargs[arg] = item._request.getfixturevalue(fixture_name)


@pytest.hookimpl(hookwrapper=True)
def pytest_generate_tests(metafunc):
    outcome = yield

    normalize_metafunc_calls(metafunc, 'funcargs')
    normalize_metafunc_calls(metafunc, 'params')
    print(metafunc._calls)


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
        if isinstance(val, MarkDecorator) and val.name == 'fixture':
            fname = val.args[0]
            nodeid = get_nodeid(metafunc.module, config.rootdir)
            fdef = fm.getfixturedefs(fname, nodeid)
            if fdef and fdef[0].params:
                for i, param in enumerate(fdef[0].params):
                    newcallspec = callspec.copy(metafunc)
                    newcallspec.params[fname] = param
                    newcallspec.indices[fname] = i
                    # TODO: sort out scope in pytest.mark.parameterize
                    newcallspec._arg2scopenum[fname] = scopenum_function
                    calls = normalize_call(newcallspec, metafunc, valtype, used_keys | set([arg]))
                    newcalls.extend(calls)
                return newcalls
        used_keys = used_keys | set([arg])
    return [callspec]


def get_nodeid(module, rootdir):
    path = py.path.local(module.__file__)
    relpath = path.relto(rootdir)
    if os.sep != "/":
        relpath = relpath.replace(os.sep, "/")
    return relpath
