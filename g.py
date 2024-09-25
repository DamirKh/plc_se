# global names here
from datetime import datetime

project_config = {}
project_changed = False
plcs = {}
units = {}
drivers = {}

def drop_project():
    project_config = {}
    project_changed = False
    plcs = {}
    units = {}
    drivers = {}


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
