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
      author='Christian Klöfver',
      author_email='christian.klofver@gmail.com',
      url='http://code.google.com/p/tumblr-cli/',
      download_url='https://tumblr-cli.googlecode.com/files/tumblr-cli-1.2.tar.gz',
      install_requires=['argparse', 'oauth2', 'tumblr2'],
      packages=['tumblr_cli'],
      entry_points={'console_scripts': ['tumblr-cli = tumblr_cli:main',
                                        'tumblr-cli-zim-tool = tumblr_cli.zim_tool:main']},
      )
