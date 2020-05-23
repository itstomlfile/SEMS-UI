import json
from functools import wraps
from flask import request
from lib import red
import pkgutil
import importlib
import glob
from types import SimpleNamespace

KEYTYPE_NONE = 0
KEYTYPE_DATA = 1
KEYTYPE_STATE = 2


def METAKEY(project_name, vertex): return project_name + \
                                          ":META:" + vertex  # Set META


def DATAKEY(project_name, ID, vertex): return project_name + \
                                              ":DATA:" + ID + ":" + vertex  # Set DATA


def STATEKEY(project_name, vertex): return project_name + \
                                           ":STATE:" + vertex  # Set STATE


def extract_cop(cop): return [[float(y.split(",")[0])
                               for y in x.split(",")] for x in cop]


def get_ids(match):
    # decode responses must be enabled in the redis connection to use this function
    id_list = []

    for key in red.keys(match + ":*"):
        _, _, id, _ = str(key).split(":")

        if id not in id_list:
            id_list.append(id)
    return id_list


def get_data(match, vertex_list):
    keys = []
    vertices = []
    data = []

    for vertex in vertex_list:
        key = match + vertex

        if red.exists(key):
            keys.append(key)
            vertices.append(vertex)

    if keys:
        data = red.mget(keys)

    return dict(zip(vertices, data))


def get_common(project_name, id):
    key = project_name + ":COMMON:" + id
    common = {}
    common.update({"name": red.get(key + ":NAME")})
    common.update({"interval": red.get(key + ":INTERVAL")})
    common.update({"timesteps": red.get(key + ":TIMESTEPS")})
    common.update({"starttime": red.get(key + ":STARTTIME")})

    return SimpleNamespace(**common) if common else {}


def clear_data(match):
    for key in red.keys(match):
        red.delete(key)


def get_meta(project_name, vertex):
    meta = None

    if red.exists(METAKEY(project_name, vertex)):
        a = red.get(METAKEY(project_name, vertex))
        meta = json.loads(a.decode('utf-8'))

    return SimpleNamespace(**meta) if meta else {}


def get_params(request):
    project_name = str(request.args.get("project"))
    vertex = str(request.args.get("vertex"))
    ID = str(request.args.get('ID'))

    if request.args.get('simplex'):
        simplex = request.args.get('simplex').split(":")
    else:
        simplex = []

    return project_name, vertex, ID, simplex


def sems(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = KEYTYPE_NONE
        # Extract parameters
        (project_name, vertex, ID, simplex) = get_params(request)
        # Get META
        asset = get_meta(project_name, vertex)
        # Get DATA
        data = get_data(project_name + ":DATA:" + ID + ":", simplex)
        # Get STATE
        state_data = get_data(project_name + ":STATE:", simplex)
        common = get_common(project_name, ID)

        # Your code to create value
        (keytype, value, res) = func(vertex, simplex, common, asset, data, state_data)

        # Remove the one that is not needed
        if keytype == KEYTYPE_DATA:
            key = DATAKEY(project_name, ID, vertex)
        elif keytype == KEYTYPE_STATE:
            key = STATEKEY(project_name, vertex)

        # Set the DATA
        if keytype in [KEYTYPE_DATA, KEYTYPE_STATE]:
            red.set(key, value)

        return res

    return wrapper


def load_modules(path, name):
    # Based on https://stackoverflow.com/questions/32420646/how-to-expose-every-name-in-sub-module-in-init-py-of-a-package
    for mod_info in pkgutil.walk_packages(path, name + '.'):
        mod = importlib.import_module(mod_info.name)

        # Emulate `from mod import *`
        try:
            names = mod.__dict__['__all__']
        except KeyError:
            names = [k for k in mod.__dict__ if not k.startswith('_')]

        globals().update({k: getattr(mod, k) for k in names})


def load_api_modules(path, name):
    res = set()

    for mod_info in pkgutil.walk_packages(path, name + "."):
        mod = importlib.import_module(mod_info.name)

        # Emulate `from mod import *`
        try:
            names = mod.__dict__['__all__']
        except KeyError:
            names = [k for k in mod.__dict__ if not k.startswith('_')]

        for k in names:
            if k[:4] == 'api_':
                res.add(getattr(mod, k))
                globals().update({k: getattr(mod, k)})

    return res
