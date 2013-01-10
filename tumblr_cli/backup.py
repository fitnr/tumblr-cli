'''
Created on Jan 8, 2013

@author: chrisk
'''

import argparse
import traceback
import pdb
import os
import json
import re
import urllib
import tumblr_cli
import git
import fnmatch
import glob
import sys


def get_argparser():
    argparser = argparse.ArgumentParser(description=
                                        'Does backup of your Tumblr blog.')
    argparser.add_argument('blog', action='store',
                           help="The blog to act on. E.g 'staff.tumblr.com' or 'www.klofver.eu'")
    argparser.add_argument('--out_mode', action='store', default='meta-img-html',
                           choices=['meta-img-html', 'blob-file', 'one-post-blobs'],
                           help="May be one of: %(choices)s Default: %(default)s")
    argparser.add_argument('--out_path', action='store', default='./%(id)s.%(blog_name)s.%(slug)s',
                           help="Path-pattern where backup will be saved. Default: %(default)s")
    argparser.add_argument('--post_type', action='store', default='all',
                           choices=['all', 'text', 'quote', 'link', 'answer', 'video', 'audio', 'photo', 'chat'],
                           help=("The post type to backup. May be one of: %(choices)s Default: %(default)s"))
    argparser.add_argument('--param', metavar='KEY=VAL', action='append',
                           help=('Extra parameter. See valid parameters and values'
                                 ' here: http://www.tumblr.com/api_docs'))
    argparser.add_argument('--pdb', action='store_true', default=False,
                           help='Puts you in pdb mode if any exceptions are raised.')
    argparser.add_argument('--config', metavar='FILE', default="~/.tumblr-cli/config",
                           help="Configuration file. Default: [%(default)s]")
    argparser.add_argument('--rmdel', action='store_true', default=False,
                           help='Removes files not present on Tumblr any more.')
    argparser.add_argument('--root', metavar='DIR', action='store', default="./",
                           help='Store the files in this directory. Note that the '
                           'directory should be dedicated to this backup, non-recognized '
                           'files will be removed except if kept in the directory '
                           '"BACKUP-EXTRA". Default: %(default)s')
    argparser.add_argument('--git', action='store_true', default=False,
                           help='Whether backup should be stored in git. Recommended to use --rmdel '
                           'in combination with this. So that files will be moved if renamed.')
    argparser.add_argument('--git_msg', metavar='COMMIT_MSG', action='store',
                           default="%(backup_cmd)s; %(blog_updated)s",
                           help="The git commit message. Default '%(default)s'")
    return argparser

class BackupHandler(object):
    BACKUP_EXTRA = "./BACKUP-EXTRA"

    def __init__(self, p_root_dir):
        self.root_dir = p_root_dir
        self.old_backup_files = self.get_list_of_files(p_root_dir,
                                                       ["./.git", self.BACKUP_EXTRA])
        self.strip_double_slashes(self.old_backup_files)
        self.backup_files = []
        self.updated_files = []
        self.deleted_files = []
        self.added_files = []
        self.blog_dict = {'backup_cmd': "'" + "' '".join(sys.argv) + "'"}

    def get_list_of_files(self, p_dir, p_exclude=None, p_trav_pos="./"):
        ret_list = []
        if p_exclude == None:
            p_exclude = []
        dirlist = os.listdir(p_dir)
        for item in dirlist:
            path = "%s/%s" % (p_dir, item)
            trav_pos = "%s%s" % (p_trav_pos, item)
            do_exclude = False
            for exclude in p_exclude:
                if fnmatch.fnmatch(trav_pos, exclude):
                    do_exclude = True
                    break
            if do_exclude:
                continue
            if os.path.isdir(path):
                ret_list += self.get_list_of_files(path, p_exclude, trav_pos + "/")
            else:
                ret_list.append(trav_pos)
        return ret_list

    def backup(self, p_posts, p_mode, p_path):
        assert p_posts['meta']['status'] == 200, "Unexpected response meta: %s" % p_posts['meta']
        self.blog_dict.update([("blog_%s" % key, val) for (key, val) in p_posts['response']['blog'].items()])
        if p_mode == 'blob-file':
            save_path = p_path % self.blog_dict
            self.save_file(save_path, p_posts['response'])
        elif p_mode == 'one-post-files':
            for post_dict in p_posts['response']['posts']:
                path_dict = dict(post_dict)
                path_dict.update(self.blog_dict)
                save_path = p_path % path_dict
                self.save_file(save_path, post_dict)
        elif p_mode == 'meta-img-html':
            for post_dict in p_posts['response']['posts']:
                path_dict = dict(post_dict)
                path_dict.update(self.blog_dict)
                # [u'body', u'highlighted', u'reblog_key', u'format', u'timestamp', u'note_count', u'tags', u'id', u'post_url', u'state', u'short_url', u'date', u'title', u'type', u'slug', u'blog_name']
                # [u'blog_updated', u'blog_posts', u'blog_ask', u'blog_url', u'blog_share_likes', 'backup_cmd', u'blog_name', u'blog_title', u'blog_description']
                save_path = p_path % path_dict
                meta_dict = dict(post_dict)
                if meta_dict['type'] == 'text':
                    body = meta_dict.pop('body')
                elif meta_dict['type'] == 'photo':
                    body = meta_dict.pop('caption')
                elif meta_dict['type'] == 'quote':
                    body = meta_dict.pop('source')
                else:
                    body = None
                meta_path = "%s.meta" % save_path
                if self.is_updated(meta_path, meta_dict):
                    self.save_file(meta_path, meta_dict, p_check=False)
                    if body:
                        self.save_file("%s.html" % save_path, body, p_check=False)
                    self.save_images("%s.img" % save_path, post_dict)
                else:
                    self.register_file("%s.meta" % save_path, False)
                    if body:
                        self.register_file("%s.html" % save_path, False)
                    self.register_file("%s.img/*" % save_path, False)

    def register_file(self, p_file, p_updated=True):
        files = glob.glob(p_file)
        if len(files) > 1:
            for f in files:
                self.register_file(f, p_updated)
        elif len(files) == 1:
            stripped_file = self.strip_double_slashes(files[0])
            self.backup_files.append(stripped_file)
            if not stripped_file in self.old_backup_files:
                self.added_files.append(stripped_file)
            if p_updated:
                print "Saved file '%s'." % stripped_file
                self.updated_files.append(stripped_file)

    def save_file(self, p_path, p_content, p_check=True):
        if p_path == '-':
            print json.dumps(p_content)
        elif not p_check or self.is_updated(p_path, p_content):
            directory = os.path.dirname(os.path.expanduser(p_path))
            if not os.path.exists(directory):
                os.makedirs(directory)
            self.save_str_file(p_path, json.dumps(p_content))
            self.register_file(p_path, True)
        else:
            self.register_file(p_path, False)

    def save_str_file(self, p_path, p_content):
        openfile = open(p_path, "w+")
        openfile.write(p_content)
        openfile.close()

    def is_updated(self, p_file, p_post):
        """ Check whether the post is new in comparison to already existing file.
        """
        if not os.path.exists(p_file):
            return True
        openfile = open(p_file, "r")
        if p_post.has_key('blog'):
            blog_updated_ts = p_post['blog']['updated']
            file_updated_ts = json.load(openfile)
        else:
            blog_updated_ts = int(p_post['timestamp'])
            file_updated_ts = int(json.load(openfile)['timestamp'])
        openfile.close()
        return blog_updated_ts > file_updated_ts

    def save_images(self, p_dir, p_post_dict):
        if p_post_dict['type'] == 'text':
            image_urls = self.extract_image_urls_from_text(p_post_dict)
        elif p_post_dict['type'] == 'photo':
            image_urls = self.extract_image_urls_from_photo(p_post_dict)
        else:
            image_urls = []
        for image_url in image_urls:
            self.save_image(p_dir, image_url)

    def save_image(self, p_dir, p_image_url):
        filename = self.url2filename(p_image_url)
        filepath = "%s/%s" % (p_dir, filename)
        if not os.path.isfile(filepath):
            if not os.path.exists(p_dir):
                os.makedirs(p_dir)
            urllib.urlretrieve(p_image_url, filepath)
            self.register_file(filepath, True)
        else:
            self.register_file(filepath, False)

    def url2filename(self, p_image_url):
        return p_image_url.replace("/", "_").replace(":", "_")

    def extract_image_urls_from_text(self, p_post_dict):
        return re.findall('src=\"(http://media.tumblr.com/[^\"]*)\"', p_post_dict['body'])

    def extract_image_urls_from_photo(self, p_post_dict):
        ret_list = []
        for photo_dict in p_post_dict['photos']:
            ret_list.append(photo_dict['original_size']['url'])
        return ret_list

    def strip_double_slashes(self, p_str):
        if not type(p_str) is list:
            return p_str.replace("//", "/")
        else:
            for i in range(len(p_str)):
                p_str[i] = self.strip_double_slashes(p_str[i])
            return p_str

    def remove_deleted(self):
        disappeared_files = list(set(self.old_backup_files) - set(self.backup_files))
        for f in disappeared_files:
            os.remove(f)
        self.deleted_files = disappeared_files

    def add_git_ignore_backup_extra(self, p_repo):
        backup_extra = "%s/%s" % (self.root_dir, self.BACKUP_EXTRA)
        if not os.path.exists(backup_extra):
            os.mkdir(backup_extra)
        p_repo.git.add(backup_extra)
        for git_ignore_dir in (self.root_dir, backup_extra):
            git_ignore_path = "%s/.gitignore" % git_ignore_dir
            if not os.path.exists(git_ignore_path):
                self.save_str_file(git_ignore_path, "")
            p_repo.git.add(git_ignore_path)

    def git_add_rm_commit(self, p_message):
        repo = git.Repo.init(self.root_dir)
        for rmfile in self.deleted_files:
            repo.git.rm(rmfile)
        for addfile in self.updated_files:
            repo.git.add(addfile)
        self.add_git_ignore_backup_extra(repo)
        if repo.git.status(porcelain=True) != '':
            repo.git.commit(m=p_message % self.blog_dict)
        repo.git.clean(f=True, d=True)


def main():
    parser = get_argparser()
    args = parser.parse_args()
    try:
        if args.post_type == 'all':
            args.post_type = None
        handler = tumblr_cli.TumblrHandler(os.path.expanduser(args.config))
        client = handler.get_unauthorized_client(args.blog)
        posts = client.get_blog_posts(args.post_type,
                                      tumblr_cli.param_to_dict(args.param))
        bh = BackupHandler(args.root)
        bh.backup(posts, args.out_mode, args.out_path)
        if args.rmdel:
            bh.remove_deleted()
        if args.git:
            bh.git_add_rm_commit(args.git_msg)
    except:
        print traceback.format_exc()
        if args.pdb:
            pdb.post_mortem()

if __name__ == '__main__':
    main()
