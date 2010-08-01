'''
lock.py - this file is part of S3QL (http://s3ql.googlecode.com)

Copyright (C) Nikolaus Rath <Nikolaus@rath.org>

This program can be distributed under the terms of the GNU LGPL.
'''

from __future__ import division, print_function, absolute_import

from s3ql import libc
import os
import logging
from s3ql.common import (add_stdout_logging, setup_excepthook, CTRL_NAME, QuietError)
from s3ql.optparse import OptionParser
import struct
import textwrap
import sys

log = logging.getLogger("lock")

def parse_args(args):
    '''Parse command line'''

    parser = OptionParser(
        usage="%prog [options] <directory>\n"
              "%prog --help",
        description=textwrap.dedent('''\
        Makes the given directory tree immutable. No changes of any sort can
        be performed on the tree after that. Immutable entries can only be
        deleted with s3qlrm. 
        '''))

    parser.add_option("--debug", action="store_true",
                      help="Activate debugging output")
    parser.add_option("--quiet", action="store_true", default=False,
                      help="Be really quiet")

    (options, pps) = parser.parse_args(args)

    # Verify parameters
    if len(pps) != 2:
        parser.error("Incorrect number of arguments.")
    options.name = pps[0].rstrip('/')

    return options

def main(args=None):
    '''Make directory tree immutable'''

    if args is None:
        args = sys.argv[1:]

    options = parse_args(args)

    # Initialize logging if not yet initialized
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = add_stdout_logging(options.quiet)
        setup_excepthook()  
        if options.debug:
            root_logger.setLevel(logging.DEBUG)
            handler.setLevel(logging.DEBUG)
        else:
            root_logger.setLevel(logging.INFO)     
    else:
        log.info("Logging already initialized.")

    if not os.path.exists(options.name):
        raise QuietError('%r does not exist' % options.name)
    
    parent = os.path.dirname(os.path.abspath(options.name))
    fstat_p = os.stat(parent)
    fstat = os.stat(options.name)
    
    if fstat_p.st_dev != fstat.st_dev:
        raise QuietError('%s is a mount point itself.' % options.name)
    
    ctrlfile = os.path.join(parent, CTRL_NAME)
    if not (CTRL_NAME not in libc.listdir(parent) and os.path.exists(ctrlfile)):
        raise QuietError('%s is not on an S3QL file system' % options.name)

    if os.stat(ctrlfile).st_uid != os.geteuid():
        raise QuietError('Only root and the mounting user may run s3qllock.')

    libc.setxattr(ctrlfile, 'lock', struct.pack('I', fstat.st_ino))

if __name__ == '__main__':
    main(sys.argv[1:])
