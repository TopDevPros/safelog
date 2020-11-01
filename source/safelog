#! /usr/bin/python3

'''
    Multiprocess-safe logs.

    Log server for denova.python.

    See https://docs.python.org/dev/howto/logging-cookbook.html#network-logging
        file:///usr/share/doc/python3.5/html/library/socketserver.html#module-socketserver

    To do: Drop privs. Create a user with write permission to log files.

    Copyright 2019-2020 DeNova
    Last modified: 2020-10-31

    This file is open source, licensed under GPLv3 <http://www.gnu.org/licenses/>.
'''

import argparse
import os
import os.path
import queue
import socketserver
import sys
from shutil import chown
from subprocess import CalledProcessError
from threading import Thread
from traceback import format_exc

from denova.os.command import run
from denova.os.fs import why_file_permission_denied
from denova.os.user import require_user, sudo
from denova.python.format import to_string
# constants shared with denova.python.log and safelog are
# in denova.python.log so they can be imported easily by tools
from denova.python.log import SAFELOG_HOST, SAFELOG_PORT, FIELD_SEPARATOR
# safelog itself uses the alternative logging in denova.python._log
from denova.python._log import log as tmp_log
from denova.python.times import timestamp

# must be distinct from denova.python.log.FIELD_SEPARATOR
NEWLINE_SUBSTITUTE = '\x02'

# analogous to /var/log
BASE_LOG_DIR = '/var/local/log'

# WARNING: if debug() is logging to disk, then
# setting "DEBUGGING = True" can use all your disk space
DEBUGGING = False

q = queue.Queue()

def main(args):
    if args.stop:
        stop()
    else:
        start()

def start():
    '''
        Start the safelog.

        <<< start()
        Traceback (most recent call last):
           ...
        SystemExit: This program must be run as root. Current user is ramblin.
    '''

    thread = None

    try:
        # we require running as root because we're a server and
        # so we can write to log files as the log user this lets
        # users clear out their own logs whenever they want
        require_user('root')

        thread = Thread(target=writer)
        thread.start()

        # Create the server, binding to localhost and SAFELOG_PORT
        BIND_ADDR = (SAFELOG_HOST, SAFELOG_PORT)
        server = socketserver.TCPServer(BIND_ADDR, SafelogServer)

        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()

    except KeyboardInterrupt:
        pass

    except Exception as exc:
        error(exc)

    finally:
        q.put(None)
        if thread:
            thread.join()

def stop():
    '''
        Stop the safelog.

        <<< stop()
        Traceback (most recent call last):
           ...
        SystemExit: This program must be run as root. Current user is ramblin.
    '''

    # we require running as root because we're a server
    require_user('root')

    tmp_log('stopping safelog')
    try:
        run('fuser', '--kill', f'{SAFELOG_PORT}/tcp')
    except CalledProcessError as cpe:
        tmp_log('safelog threw a CalledProcessError')
        tmp_log(cpe)
        try:
            run('killmatch', 'safelog')
        except:  # 'bare except' because it catches more than "except Exception"
            tmp_log(format_exc())
    except Exception as e:
        tmp_log('safelog threw an unexpected exception')
        tmp_log(e)
    tmp_log('safelog stopped')

def writer():
    ''' Write log entries from the queue to user log files.'''

    try:
        #debug('start writer')
        openfiles = {}

        data = q.get()
        while data is not None:

            #debug('dequeued:', data, type(data)) # DEBUG

            # empty data appears to happen when denova.python.log gets an error and
            # doesn't send the data correctly
            if data.strip():

                # data is USER PATHNAME MESSAGE, separated by FIELD_SEPARATOR
                # we want strings, not bytes
                """
                tmp_log('data: {}'.format(data))
                tmp_log('to_string(data): {}'.format(data.decode()))
                tmp_log('to_string(data).split(FIELD_SEPARATOR): {}'.format(data.decode().split(FIELD_SEPARATOR)))
                """
                # when the message has binary data, it can contain
                # extra FIELD_SEPARATORs
                # so we unpack carefully
                data = to_string(data)

                parts = data.split(FIELD_SEPARATOR)
                if len(parts) == 3:
                    user, logname, message = to_string(data).split(FIELD_SEPARATOR)
                    ok = True

                elif len(parts) > 3:
                    user, __, remainder = to_string(data).partition(FIELD_SEPARATOR)
                    logname, __, __ = remainder.partition(FIELD_SEPARATOR)
                    debug(f'bad log packet from user "{user}" for log {logname}, {len(parts)} parts')
                    ok = False

                else:
                    debug('bad log packet')
                    ok = False

                if ok:
                    debug('writer()', user, logname, message) # DEBUG

                    # decode embedded ascii linefeed
                    message = message.replace(NEWLINE_SUBSTITUTE, '\n')

                    pathname = os.path.join(BASE_LOG_DIR, user, logname)
                    if pathname not in openfiles or not os.path.exists(pathname):
                        open_log(user, pathname, openfiles)

                    debug(f"writer() {user} write to {message.rstrip()}") # DEBUG
                    logfile = openfiles[pathname]
                    try:
                        #logfile.seek(0, io.SEEK_END)
                        # the log may have been truncated, etc.
                        if (logfile.tell() != os.path.getsize(pathname)):
                            debug(f'log file size changed: {pathname}')
                            open_log(user, pathname, openfiles)

                        logfile.write(message)

                    except Exception as exc:
                        # log it, reopen the log, and retry
                        tmp_log(f'error while writing to: {pathname}')
                        tmp_log(str(exc))
                        try:
                            open_log(user, pathname, openfiles)
                            logfile = openfiles[pathname]
                            logfile.write(message)
                        except Exception as exc:
                            # log it, reopen the log, and try again
                            tmp_log(f'open log retry failed: {str(exc)}')

                    else:
                        logfile.flush()

                # debug('writer() write done')

            else:
                debug('writer() got empty data; did denova.python.log and LogHandler send it correctly?')

            q.task_done()
            data = q.get()

    except Exception as exc:
        error(exc)

    debug('writer() done')

def open_log(user, pathname, openfiles):
    '''
        Open the log for the user, creating the log dir if it doesn't exist.

        >>> from denova.os.user import getgid_name, getuid_name, whoami
        >>> if whoami() == 'root':
        ...     openfiles = {}
        ...     user = whoami()
        ...     log_dir = os.path.join(BASE_LOG_DIR, user)
        ...     if os.path.exists(log_dir):
        ...         results = run('rm', '-fr', log_dir)
        ...     open_log(user, os.path.join(log_dir, 'test.log'), openfiles)
        ...     os.path.exists(log_dir)
        ...     statinfo = os.stat(log_dir)
        ...     getuid_name(statinfo.st_uid) == user
        ...     getgid_name(statinfo.st_gid) == user
        ... else:
        ...     print(True)
        ...     print(True)
        ...     print(True)
        True
        True
        True
    '''

    debug(f'writer() open or reopen {pathname}')

    # if the log might be open, try to close it
    if pathname in openfiles:
        try:
            openfiles[pathname].close()
        except:  # 'bare except' because it catches more than "except Exception"
            pass
        finally:
            del openfiles[pathname]

    try:
        dirname = os.path.dirname(pathname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            chown(dirname, user, user)

        with sudo(user):
            openfiles[pathname] = open(pathname, 'a')
        debug(f'writer() opened {pathname}')
        assert os.path.exists(pathname) # DEBUG

    except PermissionError as pe:
        debug(pe)
        why = pathname, why_file_permission_denied(pathname, 'a')
        msg = f'open("{why}","a") failed:\n\t{pe}'
        error(msg)

def error(why):
    tmp_log(why)
    print(format_exc())
    print(str(why))
    sys.exit(why)

def debug(*args):
    ''' Output debug message to /tmp/_log.root.log. '''

    if DEBUGGING:
        parts = [timestamp()] + list(args)
        msg = '\t'.join(map(str, parts))
        print(msg)
        tmp_log(msg)

def parse_args():
    ''' Parsed command line. '''

    parser = argparse.ArgumentParser(description='Manage logs in a multiprocessing safe manner.')

    parser.add_argument('--start',
                        help="Start the safelog",
                        action='store_true')
    parser.add_argument('--stop',
                        help="Stop the safelog",
                        action='store_true')

    args = parser.parse_args()

    return args


class SafelogServer(socketserver.StreamRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):

        try:
            data = self.rfile.read()
            debug('handle() raw data:', data) # DEBUG
            if data.strip():
                q.put_nowait(data)
            else:
                debug('got empty data; did denova.python.log send it correctly?')

            """
            text = to_string(data.strip())
            # debug('raw text:', text) # DEBUG

            # encode embedded ascii linefeed so that
            # when we readline() the file we get a whole message at a time
            text = text.replace('\n', NEWLINE_SUBSTITUTE)
            # debug('newline encoded text:', text) # DEBUG

            outdata = (text + '\n').encode()
            q.put_nowait(outdata)
            """

            """
            user, pathname, message = text.split(FIELD_SEPARATOR) # DEBUG
            debug('in handle()', user, pathname, message) # DEBUG
            # debug('queued:', outdata) # DEBUG
            debug('queue size:', q.qsize()) # DEBUG
            """

            """
            # self.rfile is a file-like object created by the handler;
            # we can use e.g. readline() instead of raw recv() calls
            data = to_string(self.rfile.readline().strip())

            # Likewise, self.wfile is a file-like object used to write back
            # to the client
            # self.wfile.write('received: ' + data)
            """

        except Exception as exc:
            error(exc)


if __name__ == "__main__":
    args = parse_args()

    main(args)
