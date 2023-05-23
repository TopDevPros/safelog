
Safelog
-------

Get instant multithread, multiprocess, and multiprogram safe logs. Safelog also
has a much simpler and more powerful api than standard python logging.

Description
-----------

Safelog is simple multithread, multiprocess, multiprogram logging.

Start as many threads, subprocesses, or programs as you like that all write to the same logs. Safelog instantly creates your logs, and only lets one writer at a time write to each one. Plus it has a much simpler and more powerful api than standard python logging.

    Instant logs
    No conflicts between users or modules
    Organized logs save days or weeks debugging
    Multithread, multiprocess, and multiprogram safe
    Log exceptions and stacktraces simply
    Default log pathnames based on user and module: "/var/local/log/USER/MODULE.log"
    Easy to find the right log
    A master.log for each user shows you all log entries in order


Install
-------

Just and run it. The safeget-safelog installer will download, verify, and install Safelog.
Quick start

Start the safelog server:

        safelog


Or copy the systemd safelog.service file from your python dist-packages/safelock directory (e.g., /usr/local/lib/python3.9/dist-packages/safelog) to the /etc/systemd/system directory. Then you use the following commands to make sure Safelog is available for all of your python apps:

        systemctl enable safelog
        systemctl start safelog


How it Works
------------

Safelog has a much simpler api than standard python logging. The client code for safelog is solidlibs.python.log.

        from solidlibs.python.log import Log
        log = Log()

        log('log this safely')


Details
-------

The default log file is "/var/local/log/USER/MODULE.log". USER is the current user. MODULE is the python module using solidlibs.python.log.

Log a specified exception and its traceback:

        try:
            raise Exception('test')
        except Exception as exc:
            log(exc)


Log the current exception.

        try:
            raise Exception('test')
        except:
            log.exception()


Log the current exception without traceback.

        try:
            raise Exception('test')
        except:
            log.exception_only()


Log a stacktrace.

        log.stacktrace()


Specify a log filename. Safelog will put it in /var/local/log/USER.

        log = get('special.log')
        log('log message to special.log')


Useful when you want different modules to write to a shared log.

Specify a full log pathname.

        log = get('/tmp/special.log')
        log('log message to /tmp/special.log')


You don't get safe separation for users and modules if you specify a full log pathname.

Logging levels work as usual. The default logging level is DEBUG.

        log.debug('debugging message')
        log.info('informational message')
        log.warning('something went wrong')
        log.error('something went very wrong')

        log('same as log.debug')

Safelog automatically creates timestamped logs safely separated for each user and python module. It also logs every entry to a master log for each user.

The log defaults work especially well in complex systems. When apps run as separate users and share modules, every user and module gets their own logs. There's no conflict over which user owns a log. There are no jumbled log lines from different users or processes.

The safelog server will create directories as needed. If a program bypasses solidlibs.python.log and writes to /var/local/log, it may have to create the directories it uses.

Running a module while in the module directory may not create the log file for that module.

If you are installing Safelog from github, be sure to also install the "solidlibs" package from PyPI.
