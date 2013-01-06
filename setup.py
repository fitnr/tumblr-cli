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
      version='1.2',
      url='http://code.google.com/p/tumblr-cli/',
      author='Christian Klöfver',
      author_email='christian.klofver@gmail.com',
      install_requires=['argparse', 'oauth2', 'tumblr2'],
      py_modules=['tumblr_cli', 'tumblr_cli.zim_tool'],
      entry_points={'console_scripts': ['tumblr-cli = tumblr_cli:main',
                                        'tumblr-cli-zim-tool = tumblr_cli.zim_tool:main']},
      )
