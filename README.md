tumblr-cli
==========

Gives access to the Tumblr API from the command line.

This is a mirror of https://code.google.com/p/tumblr-cli/.

Install with:

``` prettyprint
pip install tumblr-cli
```

See my blog post here for some help to install and use: <http://www.klofver.eu/post/39789325684/tumblr-command-line-interface-tumblr-cli>

``` prettyprint
$ tumblr-cli --helpusage: tumblr-cli [-h] [--blog BLOG] [--authorize] [--post_text FILE]                  [--title TITLE] [--param KEY=VAL] [--config FILE] [--pdb]
Tumblr Command Line Interface
optional arguments:  
 -h, --help        show this help message and exit  
 --blog BLOG       The blog to act on. E.g staff.tumblr.com or www.klofver.eu  
 --authorize       Authorize to blog  
 --post_text FILE  Post a text file to your blog  
 --title TITLE     The title to be used in posts  
 --param KEY=VAL   Extra parameter. See valid parameters and values here: http://www.tumblr.com/api_docs  
 --config FILE     Configuration file  
 --pdb             Puts you in pdb mode if any exceptions are raised.
```

Blog post about tumblr-cli-backup: <http://www.klofver.eu/post/40208144381/backup-and-version-control-your-tumblr-blog-with>

``` prettyprint
$ tumblr-cli-backup --helpusage: tumblr-cli-backup [-h]
                         [--out_mode {meta-img-html,blob-file,one-post-blobs}]
                         [--out_path OUT_PATH]
                         [--post_type {all,text,quote,link,answer,video,audio,photo,chat}]
                         [--param KEY=VAL] [--pdb] [--config FILE] [--rmdel]
                         [--root DIR] [--git] [--git_msg COMMIT_MSG]
                         blog

Does backup of your Tumblr blog.

positional arguments:
  blog                  The blog to act on.

optional arguments:
  -h, --help            show this help message and exit
  --out_mode {meta-img-html,blob-file,one-post-blobs}
                        May be one of: meta-img-html, blob-file, one-post-
                        blobs Default: meta-img-html

  --out_path OUT_PATH   Path-pattern where backup will be saved. Default:
                        ./%(id)s.%(blog_name)s.%(slug)s
  --post_type {all,text,quote,link,answer,video,audio,photo,chat}
                        The post type to backup. May be one of: all, text,                        quote, link, answer, video, audio, photo, chat
                        Default: all
  --param KEY=VAL       Extra parameter. See valid parameters and values here:
                        http://www.tumblr.com/api_docs
  --pdb                 Puts you in pdb mode if any exceptions are raised.
  --config FILE         Configuration file. Default: [~/.tumblr-cli/config]
  --rmdel               Removes files not present on Tumblr any more.
  --root DIR            Store the files in this directory. Note that the
                        directory should be dedicated to this backup, non-
                        recognized files will be removed except if kept in the
                        directory "BACKUP-EXTRA". Default: ./
  --git                 Whether backup should be stored in git. Recommended to
                        use --rmdel in combination with this. So that files
                        will be moved if renamed.
  --git_msg COMMIT_MSG  The git commit message. Default '%(backup_cmd)s;                        %(blog_updated)s'
```

For some guidance about the Zim tool, look here: <http://www.klofver.eu/post/39885082363/post-to-tumblr-from-zim-desktop-wiki-with-tumblr-cli>

``` prettyprint
$ tumblr-cli-zim-tool -husage: tumblr-cli-zim-tool [-h] [--title TITLE] [--param KEY=VAL] [--pdb]                           [--config FILE] [--export_cmd CMD]
                           blog directory notebook
Post to Tumblr from Zim Desktop Wiki. Should be used as a Zim custom tool with
the command: tumblr-cli-zim-tool <blog> %d %n
positional arguments:
  blog
              The blog to act on. E.g 'staff.tumblr.com' or
                     'www.klofver.eu'
   directory          %d
   notebook            %n

  optional arguments:
  -h, --help        show this help message and exit
  --title TITLE     The title to be used in posts
  --param KEY=VAL   Extra parameter. See valid parameters and values here:
                    http://www.tumblr.com/api_docs
  --pdb             Puts you in pdb mode if any exceptions are raised.
  --config FILE     Configuration file. Default: [~/.tumblr-cli/config]
  --export_cmd CMD  Command for exporting the Zim page. Default: [zim --export                  
  --format html %s %s]
```
