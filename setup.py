#!/usr/bin/python
# encoding: utf-8
'''
Created on Jan 5, 2013

http://code.google.com/p/tumblr-cli/

@author: chrisk
'''

from distutils.core import setup
import tumblr_cli

setup(name='tumblr-cli',
      description='Python Tumblr CLI. Command line interface client for the Tumblr API.',
      version=tumblr_cli.__version__,
      author='Christian Klöfver',
      author_email='christian.klofver@gmail.com',
      license='GPL v2',
      url='http://code.google.com/p/tumblr-cli/',
      download_url='https://tumblr-cli.googlecode.com/files/tumblr-cli-%s.tar.gz' % tumblr_cli.__version__,
      install_requires=['argparse', 'oauth2', 'tumblr2', 'GitPython', 'poster', 'lxml'],
      packages=['tumblr_cli'],
      entry_points={'console_scripts': ['tumblr-cli = tumblr_cli:main',
                                        'tumblr-cli-zim-tool = tumblr_cli.zim_tool:main',
                                        'tumblr-cli-backup = tumblr_cli.backup:main']},
      )
