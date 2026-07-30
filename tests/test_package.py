"""Smoke tests for the project bootstrap."""

import sys
from importlib import import_module
from importlib.metadata import version

import httpx
import psycopg
import sqlalchemy
from pydantic import BaseModel
from pydantic_settings import BaseSettings

import homesearch


def test_package_is_installed_from_src_layout() -> None:
    assert homesearch.__version__ == version("homesearch")


def test_runtime_uses_approved_python_series() -> None:
    assert sys.version_info[:2] == (3, 14)


def test_accepted_runtime_dependencies_load_on_python_314() -> None:
    assert callable(httpx.Client)
    assert import_module("lxml.html").__name__ == "lxml.html"
    assert issubclass(BaseSettings, BaseModel)
    assert psycopg.__version__
    assert sqlalchemy.__version__
