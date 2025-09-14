#!/usr/bin/python

from distutils.core import setup

setup_args = {
    "name": 'damicore',
    "version": '0.1.0',
    "author": 'Bruno Kim Medeiros Cesar',
    "author_email": 'brunokim@icmc.usp.br',
    "license": 'GPLv2',
    "requires": ['igraph', 'munkres'],
    "packages": ['damicore'],
    }

setup(**setup_args)
