#!/usr/bin/python
# encoding: utf-8
'''
Created on Jan 4, 2013

http://code.google.com/p/tumblr-cli/

@author: christian.klofver@gmail.com
'''

import tumblr
import tumblr.oauth as real_tumblr_oauth
import oauth2
tumblr.oauth = oauth2  # Because relative import is blocking tumblr lib from functioning
import ConfigParser
import argparse
import time
import pdb
import os.path
import traceback
import urllib
import sys
import urllib2
import urlparse
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

class TumblrHandler(object):
    EXPIRY_TIME = 86400000  # TODO: dummy value, how long is really the expiry time?

    def __init__(self, p_config_file):
        self.config_file = p_config_file
        self.cp = ConfigParser.ConfigParser()
        self.cp.read(self.config_file)

    def post_text(self, p_blog, p_file, p_title, p_params):
        if p_file == "-":
            text = sys.stdin.read()
        else:
            openfile = open(p_file)
            text = openfile.read()
            openfile.close()
        params = {'type':'text', 'state':'draft', 'title':p_title, 'body':text}
        if p_params:
            params.update(p_params)
        print self.post(p_blog, params)

    def post_image(self, p_blog, p_file, p_caption, p_params):
        openfile = open(p_file, 'rb')
        params = {'type':'photo', 'state':'draft', 'caption':p_caption, 'data':openfile}
        if p_params:
            params.update(p_params)
        print self.post_photo(p_blog, params)
        openfile.close()

    def post(self, p_blog, p_params):
        """ Post to blog, see defined params here: http://www.tumblr.com/api_docs#posting
        """
        client = self.get_client(p_blog)
        return client.create_post(p_params)

    def post_photo(self, p_blog, post):
        register_openers()
        url = "http://api.tumblr.com/v2/blog/%s/post" % p_blog
        open_file = post['data']
        del(post['data'])
        req = oauth2.Request.from_consumer_and_token(self.get_consumer(),
                                                     token=self.get_access_token(p_blog),
                                                     http_method="POST",
                                                     http_url=url,
                                                     parameters=post)
        req.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), self.get_consumer(), self.get_access_token(p_blog))
        compiled_postdata = req.to_postdata()
        all_upload_params = urlparse.parse_qs(compiled_postdata, keep_blank_values=True)
        for key, val in all_upload_params.iteritems():
            all_upload_params[key] = val[0]
        all_upload_params['data'] = open_file
        datagen, headers = multipart_encode(all_upload_params)
        request = urllib2.Request(url, datagen, headers)
        respdata = urllib2.urlopen(request).read()
        return respdata

    def get_client(self, p_blog):
        return tumblr.TumblrClient(p_blog, self.get_consumer(), self.get_access_token(p_blog))

    def get_unauthorized_client(self, p_blog):
        return tumblr.TumblrClient(p_blog, self.get_consumer())

    def get_consumer(self):
        return oauth2.Consumer(self.cp.get('consumer', 'key'),
                               self.cp.get('consumer', 'secret'))

    def get_access_token(self, p_blog):
        return oauth2.Token(self.cp.get(p_blog, 'access_key'),
                            self.cp.get(p_blog, 'access_secret'))

    def authorize(self, p_blog, p_force):
        consumer_key = self.get_set('consumer', 'key')
        consumer_secret = self.get_set('consumer', 'secret')
        tumblr_oauth = real_tumblr_oauth.TumblrOAuthClient(consumer_key,
                                                           consumer_secret)
        self.get_oauth_access(tumblr_oauth, p_blog, p_force)
        self.write_config()

    def write_config(self):
        f = open(self.config_file, 'w+')
        self.cp.write(f)
        f.close()

    def get_set(self, p_section, p_option, p_ask=True):
        value = None
        if self.cp.has_option(p_section, p_option):
            value = self.cp.get(p_section, p_option)
        else:
            value = None
            print "No value for %s.%s found.\n" % (p_section, p_option)
        if value == None and p_ask:
            value = raw_input('What is the value for %s.%s? ' % (p_section, p_option))
            if not self.cp.has_section(p_section):
                self.cp.add_section(p_section)
            self.cp.set(p_section, p_option, value)
        return value

    def get_oauth_access(self, p_tumblr_oauth, p_blog, p_force):
        access_key = None
        access_secret = None
        oauth_verifier_ts = None
        try:
            if not p_force:
                access_key = self.cp.get(p_blog, 'access_key')
                access_secret = self.cp.get(p_blog, 'access_secret')
                oauth_verifier_ts = self.cp.getint(p_blog, 'oauth_verifier_ts')
        except:
            pass
        if (access_key == None or access_secret == None or
            oauth_verifier_ts == None or
            oauth_verifier_ts + self.EXPIRY_TIME < time.time()):
            authorize_url = self.get_authorize_url(p_tumblr_oauth)
            print "Visit: %s" % authorize_url
            oauth_verifier = raw_input('What is the oauth_verifier? ')
            if not self.cp.has_section(p_blog):
                self.cp.add_section(p_blog)
            access_token = p_tumblr_oauth.get_access_token(oauth_verifier)
            access_key = access_token.key
            access_secret = access_token.secret
            self.cp.set(p_blog, 'oauth_verifier', oauth_verifier)
            self.cp.set(p_blog, 'oauth_verifier_ts', int(time.time()))
            self.cp.set(p_blog, 'access_key', access_key)
            self.cp.set(p_blog, 'access_secret', access_secret)
        return (access_key, access_secret)

    def get_authorize_url(self, p_tumblr_oauth):
        return (p_tumblr_oauth.get_authorize_url() + "&" +
                urllib.urlencode({'oauth_callback':
                                  "http://www.klofver.eu/tumblr-cli"}))

def get_argparser():
    argparser = argparse.ArgumentParser(description='Tumblr Command Line Interface')
    argparser.add_argument('--blog', action='store', metavar='BLOG',
                           help='The blog to act on. E.g staff.tumblr.com or www.klofver.eu')
    argparser.add_argument('--authorize', action='store_true', default=False,
                           help='Authorize to blog')
    argparser.add_argument('--post_text', metavar='FILE', help='Post a text file to your blog')
    argparser.add_argument('--post_image', metavar='FILE', help='Post a photo file to your blog')
    argparser.add_argument('--title', action='store', default='tumblr-cli post',
                           help='The title to be used in posts')
    argparser.add_argument('--param', metavar='KEY=VAL', action='append',
                           help=('Extra parameter. See valid parameters and values'
                                 ' here: http://www.tumblr.com/api_docs'))
    argparser.add_argument('--forceauth', action='store_true', default=False,
                           help='Reauthorize to blog even if there already is a valid access token.')
    argparser.add_argument('--config', metavar='FILE', default="~/.tumblr-cli/config",
                           help="Configuration file. Default: [%(default)s]")
    argparser.add_argument('--pdb', action='store_true', default=False,
                           help='Puts you in pdb mode if any exceptions are raised.')
    return argparser

def param_to_dict(p_list):
    if p_list == None:
        return {}
    ret_list = []
    for pair in p_list:
        ret_list.append(pair.split("=", 1))
    return dict(ret_list)

def make_config_structure(p_requested_config_file, p_default_config_file):
    confdir = os.path.dirname(os.path.expanduser(p_requested_config_file))
    if p_requested_config_file == p_default_config_file:
        if not os.path.exists(confdir):
            os.makedirs(confdir)
    else:
        if not os.path.exists(confdir):
            print "No such directory: %s" % confdir
            exit(4)

def main():
    parser = get_argparser()
    args = parser.parse_args()
    try:
        make_config_structure(args.config,
                              parser.get_default('config'))
        handler = TumblrHandler(os.path.expanduser(args.config))
        if args.blog == None:
            print "No blog to act on. Specify --blog=<BLOG>"
            exit(9)
        if args.authorize or args.forceauth:
            handler.authorize(args.blog, args.forceauth)
        if args.post_text:
            handler.post_text(args.blog,
                              args.post_text,
                              args.title,
                              param_to_dict(args.param))
        if args.post_image:
            handler.post_image(args.blog,
                               args.post_image,
                               args.title,
                               param_to_dict(args.param))
    except:
        print traceback.format_exc()
        if args.pdb:
            pdb.post_mortem()

if __name__ == '__main__':
    main()

