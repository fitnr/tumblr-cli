#!/usr/bin/python
# encoding: utf-8
'''
Created on Jan 4, 2013

http://code.google.com/p/tumblr-cli/

@author: christian.klofver@gmail.com
'''

import tumblr
from tumblr.oauth import TumblrOAuthClient
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
import lxml.etree
import re
import tumblr_cli


class TumblrHandler(object):
    EXPIRY_TIME = 86400000  # TODO: dummy value, how long is really the expiry time?

    def __init__(self, p_config_file):
        self.config_file = p_config_file
        self.cp = ConfigParser.ConfigParser()
        self.cp.read(self.config_file)
        self.xpath_dict = None
        self.regex_dict = None
        self.body = None
        self.is_dry_run = False

    def post_text(self, p_blog, p_file, p_title, p_params):
        extracted_dict = self.extract_dict(p_file)
        if self.body:
            text = self.body % extracted_dict
        else:
            text = self.get_str_from_file(p_file)
        title = p_title % extracted_dict
        self.post_text_str(p_blog, text, title, p_params)

    def extract_dict(self, p_source):
        ret_list = [('n', '\n')]
        if self.xpath_dict == None or self.regex_dict == None:
            return dict(ret_list)
        if p_source == '-':
            source = sys.stdin
        else:
            source = p_source
        if self.xpath_dict:
            tree = lxml.etree.parse(source)
            for key, xpath in self.xpath_dict.items():
                xpath_res = tree.xpath(xpath)
                if len(xpath_res) > 1:
                    # TODO: Add index to key(make more keys) instead of setting list?
                    ret_list.append((key, xpath_res))
                elif len(xpath_res) == 1:
                    ret_list.append((key, xpath_res[0].encode('utf-8')))
        if self.regex_dict:
            source_str = self.get_str_from_file(p_source)
            for key, regex in self.regex_dict.items():
                found = re.findall(regex, source_str)
                if len(found) > 0:
                    value = found[0].encode('utf-8')
                else:
                    value = ""
                ret_list.append((key, value))
        return dict(ret_list)

    def is_duplicate(self, p_blog, p_match_pairs, p_type=None):
        client = self.get_client(p_blog)
        posts_iter = get_all_blog_posts(client, p_type)
        for posts in posts_iter:
            for post in posts['response']['posts']:
                match = True
                for key, value in p_match_pairs:
                    if post.get(key) != value:
                        match = False
                        break
                if match == True:
                    return True
        return False

    def set_dry_run(self, p_is_dry_run):
        self.is_dry_run = p_is_dry_run

    def set_body(self, p_string):
        self.body = p_string

    def set_xpath_dict(self, p_xpath_dict):
        self.xpath_dict = p_xpath_dict

    def set_regex_dict(self, p_regex_dict):
        self.regex_dict = p_regex_dict

    def get_str_from_file(self, p_file):
        if p_file == "-":
            text = sys.stdin.read()
        else:
            openfile = open(p_file)
            text = openfile.read()
            openfile.close()
        return text

    def delete_post(self, p_blog, p_post_id):
        if self.is_dry_run:
            print "Would have deleted post: %s" % p_post_id
            return
        client = self.get_client(p_blog)
        return client.delete_post(p_post_id)

    def list_posts(self, p_blog, p_format, p_params):
        client = self.get_client(p_blog)
        post_iter = get_all_blog_posts(client, post_type=None, request_params=p_params, p_bare_posts=True)
        for post in post_iter:
            post_print_dict = {'blob': post, 'n': '\n'}
            post_print_dict.update(post)
            sys.stdout.write((p_format % post_print_dict).encode("UTF-8"))

    def post_text_str(self, p_blog, p_text, p_title, p_params):
        params = {'type':'text', 'state':'draft', 'title':p_title, 'body':p_text}
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
        if self.is_dry_run:
            print p_params
            return
        client = self.get_client(p_blog)
        return client.create_post(p_params)

    def post_photo(self, p_blog, p_post):
        if self.is_dry_run:
            print p_post
            return
        register_openers()
        url = "http://api.tumblr.com/v2/blog/%s/post" % p_blog
        post = list(p_post)
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
        try:
            tumblr_oauth = TumblrOAuthClient(consumer_key, consumer_secret)
            self.get_oauth_access(tumblr_oauth, p_blog, p_force)
            self.write_config()
        except:
            sys.stderr.write("\nFailed to get access keys. Please make sure you consumer "
                             "key and secret are correct and try authorize again.\n")

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
    argparser = argparse.ArgumentParser(description='Tumblr Command Line Interface. Version %s' % tumblr_cli.__version__)
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
    argparser.add_argument('--xpath', metavar='KEY=XPATH', action='append',
                           help='Xpaths for building body & title from xml')
    argparser.add_argument('--regex', metavar='KEY=REGEX', action='append',
                           help='Regex for building body & title from xml')
    argparser.add_argument('--body', metavar='STRING', action='store', default=None,
                           help='The body to be sent. If not set, the raw text in the file is sent.')
    argparser.add_argument('--forceauth', action='store_true', default=False,
                           help='Reauthorize to blog even if there already is a valid access token.')
    argparser.add_argument('--config', metavar='FILE', default="~/.tumblr-cli/config",
                           help="Configuration file. Default: [%(default)s]")
    argparser.add_argument('--pdb', action='store_true', default=False,
                           help='Puts you in pdb mode if any exceptions are raised.')
    argparser.add_argument('--dry', action='store_true', default=False,
                           help='Dry run. Doesn\'t post anything.')
    argparser.add_argument('--duplicate-check', action='store_true', default=False,
                           help='Checks whether a post with the title already exists, '
                           'and if so, refuses to post it.')
    argparser.add_argument('--delete_post', metavar='POST_ID',
                           help='Deletes the post with given id from your blog')
    argparser.add_argument('--list_posts', metavar='OUTPUT_FORMAT',
                           help="Lists the posts of your blog. Example format: '%%(blob)%%(n)s'")
    return argparser

def get_all_blog_posts(p_client, post_type=None, request_params=None, p_bare_posts=False):
    offset = 0
    if request_params == None:
        request_params = {}
    while True:
        request_params.update({'offset': offset})
        twenty = p_client.get_blog_posts(post_type, request_params)
        if p_bare_posts:
            for post in twenty['response']['posts']:
                yield post
        else:
            yield twenty
        if len(twenty['response']['posts']) != 20:
            break
        else:
            offset += 20

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
        if args.dry:
            handler.set_dry_run(True)
        if args.authorize or args.forceauth:
            handler.authorize(args.blog, args.forceauth)
        elif args.post_text:
            handler.set_body(args.body)
            handler.set_xpath_dict(param_to_dict(args.xpath))
            handler.set_regex_dict(param_to_dict(args.regex))
            if (args.duplicate_check and
                handler.is_duplicate(args.blog, [('title', args.title)])):
                print ("A post with the title '%s' already exists. "
                       "Not posting it." % args.title)
            else:
                handler.post_text(args.blog,
                                  args.post_text,
                                  args.title,
                                  param_to_dict(args.param))
        elif args.post_image:
            handler.post_image(args.blog,
                               args.post_image,
                               args.title,
                               param_to_dict(args.param))
        elif args.delete_post:
            print handler.delete_post(args.blog, args.delete_post)
        elif args.list_posts:
            handler.list_posts(args.blog, p_format=args.list_posts, p_params=param_to_dict(args.param))
        else:
            print "Nothing to do.\n"
    except:
        print traceback.format_exc()
        if args.pdb:
            pdb.post_mortem()

if __name__ == '__main__':
    main()

