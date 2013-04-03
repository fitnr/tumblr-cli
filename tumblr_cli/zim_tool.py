'''
Created on Jan 6, 2013

@author: chrisk
'''
import argparse
import tumblr_cli.tumblr_client
import traceback
import pdb
import tempfile
import subprocess
import os.path


def get_argparser():
    argparser = argparse.ArgumentParser(description=
                                        'Post to Tumblr from Zim Desktop Wiki. \n'
                                        'Should be used as a Zim custom tool with the command:\n'
                                        'tumblr-cli-zim-tool <blog> %d %n')
    argparser.add_argument('blog', action='store', help="The blog to act on. E.g 'staff.tumblr.com' or 'www.klofver.eu'")
    argparser.add_argument('directory', default=False, help='%%d')
    argparser.add_argument('notebook', help='%%n')
    argparser.add_argument('--title', action='store', default='tumblr-cli post',
                           help='The title to be used in posts')
    argparser.add_argument('--param', metavar='KEY=VAL', action='append',
                           help=('Extra parameter. See valid parameters and values'
                                 ' here: http://www.tumblr.com/api_docs'))
    argparser.add_argument('--pdb', action='store_true', default=False,
                           help='Puts you in pdb mode if any exceptions are raised.')
    argparser.add_argument('--config', metavar='FILE', default="~/.tumblr-cli/config",
                           help="Configuration file. Default: [%(default)s]")
    argparser.add_argument('--export_cmd', metavar='CMD', default="zim --export --format html %s %s",
                           help="Command for exporting the Zim page. Default: [%(default)s]")
    return argparser

def export_to_tmp_file(p_export_cmd):
    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    subprocess.call(p_export_cmd, stdout=tmpfile, shell=True)
    tmpfile.close()
    return tmpfile.name

def get_page(p_notebook, p_directory):
    return os.path.relpath(p_directory, p_notebook).replace('/', ':')

def main():
    parser = get_argparser()
    args = parser.parse_args()
    try:
        page = get_page(args.notebook, args.directory)
        tmpfile = export_to_tmp_file(args.export_cmd % (args.notebook, page))
        print tmpfile
        handler = tumblr_cli.tumblr_client.TumblrHandler(os.path.expanduser(args.config))
        handler.post_text(args.blog,
                          tmpfile,
                          args.title,
                          tumblr_cli.tumblr_client.param_to_dict(args.param))
    except:
        print traceback.format_exc()
        if args.pdb:
            pdb.post_mortem()

if __name__ == '__main__':
    main()
