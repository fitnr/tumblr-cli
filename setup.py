#!/usr/bin/python
# encoding: utf-8
'''
Created on Jan 5, 2013

http://code.google.com/p/tumblr-cli/

@author: chrisk
'''

from distutils.core import setup
setup(name='tumblr-cli',
      description='Python Tumblr CLI',
      version='1.0',
      url='http://code.google.com/p/tumblr-cli/',
      author='Christian Klöfver',
      author_email='christian.klofver@gmail.com',
      install_requires=['oauth2', 'tumblr2'],
      py_modules=['tumblr-cli'],
      )
