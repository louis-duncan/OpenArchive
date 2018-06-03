#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tempfile import gettempdir, mkstemp, mkdtemp
from public import public

__all__ = ["TMPDIR"]

public(gettempdir)

TMPDIR = gettempdir()


@public
def tempfile():
    """Create temp file"""
    return mkstemp()[1]


@public
def tempdir():
    """create temp dir"""
    return mkdtemp()
