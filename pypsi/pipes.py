#
# Copyright (c) 2014, Adam Meily
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
# * Neither the name of the {organization} nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#


import threading
import sys


class ThreadLocalStream(object):
    '''
    A stream wrapper that is thread-local. This class enables thread-based pipes
    by wrapping :attr:`sys.stdout`, :attr:`sys.stderr`, and :attr:`sys.stdin`
    and making access to them thread-local. This allows each thread to,
    potentially, each thread to write to a different stream.
    '''

    def __init__(self, target, width=None, isatty=None):
        '''
        :param file target: the original target stream (typically either
            :attr:`sys.stdout`, :attr:`sys.stderr`, and :attr:`sys.stdin`).
        :param int width: the width of the stream in characters, this attribute
            determines if word wrapping is enabled and how wide the lines are.
        :param bool isatty: whether the underlying stream is a tty stream, which
            supports ANSI escape cdes.
        '''

        #: A tuple of: (target, width, isatty)
        self._target = (target, width, isatty)
        self._proxies = {}

    def _get_target(self):
        '''
        Get the target tuple for the current thread.

        :returns tuple: (target, width, isatty).
        '''

        return self._proxies.get(threading.current_thread().ident, self._target)

    def _get_target_stream(self):
        '''
        :returns file: the target stream for the current thread.
        '''

        return self._get_target()[0]

    @property
    def width(self):
        '''
        :returns int: current thread's stream width, in characters.
        '''
        return self._get_target()[1]

    def isatty(self):
        '''
        :returns bool: whether the underlying stream for the current thread is
            a tty stream and support ANSI escape codes.
        '''

        s = self._get_target()
        return s[2] if s[2] is not None else s[0].isatty()

    def __getattr__(self, name):
        return getattr(self._get_target()[0], name)

    def __hasattr__(self, name):
        attrs = ('width', 'isatty', '_proxy', '_unproxy', '_get_target',
                 '_get_target_stream', '_proxies', '_target')

        return True if name in attrs else hasattr(self._get_target_stream(), name)

    def _proxy(self, target, width=None, isatty=None):
        '''
        Set a thread-local stream.

        :param file target: the target stream.
        :param int width: the stream width, in characters.
        :param bool isatty: whether the target stream is a tty stream.
        '''

        self._proxies[threading.current_thread().ident] = (target, width, isatty)

    def _unproxy(self, ident=None):
        '''
        Delete the proxy for a thread.

        :param int ident: the thread's :attr:`~threading.Thread.ident`
            attribute, or :const:`None` if the current thread's  proxy is being
            deleted.
        '''

        ident = ident or threading.current_thread().ident
        if ident in self._proxies:
            del self._proxies[ident]


        def ansi_format(self, tmpl, **kwargs):
            '''
            Format a string that contains ansi code terms. This function allows
            the following string to be the color red:

            ``sys.stdout.ansi_format("{red}Hello, {name}{reset}", name="Adam")``

            The :data:`pypsi.format.AnsiCodesSingleton.codes` dict contains all
            valid ansi escape code terms. If the current stream does not support
            ansi escape codes, they are dropped from the template prior to
            printing.

            :param str tmpl: the string template
            '''

            atty = self.isatty()
            for (name, value) in kwargs.items():
                if isinstance(value, AnsiCode):
                    kwargs[name] = str(value) if atty else ''

            for (name, code) in AnsiCodes.codes.items():
                kwargs[name] = code.code if atty else ''

            return tmpl.format(**kwargs)

        def ansi_format_prompt(self, tmpl, **kwargs):
            '''
            Format a string that contains ansi code terms. This function allows
            performs the same formatting as :meth:`ansi_format`, except this is
            intended for formatting strings in prompt by calling
            :meth:`pypsi.stream.AnsiCode.prompt` for each code.
            '''

            atty = self.isatty()
            for (name, value) in kwargs.items():
                if isinstance(value, AnsiCode):
                    kwargs[name] = value.prompt() if atty else ''

            for (name, code) in AnsiCodes.codes.items():
                kwargs[name] = code.prompt() if atty else ''

            return tmpl.format(**kwargs)

        def render(self, parts, prompt=False):
            '''
            Render a list of objects as  single string. This method is the
            string version of the :meth:`print` method. Also, this method will
            honor the current thread's :meth:`isatty` when rendering ANSI escape
            codes.

            :param list parts: list of object to render.
            :param bool prompt: whether to render
                :class:`~pypsi.stream.AnsiCode` objects as prompts or not.
            :returns str: the rendered string.
            '''
            r = []
            for part in parts:
                if isinstance(part, AnsiCode):
                    if self.isatty():
                        if prompt:
                            r.append(part.prompt())
                        else:
                            r.append(str(part))
                    elif part.s:
                        r.append(part.s)
                else:
                    r.append(str(part))
            return ''.join(r)



class InvocationThread(threading.Thread):
    '''
    An invocation of a command from the command line interface.
    '''

    def __init__(self, shell, invoke, stdin=None, stdout=None, stderr=None):
        '''
        :param pypsi.shell.Shell shell: the active shell.
        :param pypsi.cmdline.CommandInvocation invoke: the invocation to
            execute.
        :param stream stdin: override the invocation's stdin stream.
        :param stream stdout: override the invocation's stdout stream.
        :param stream stderr; override the invocation's stder stream.
        '''

        super(InvocationThread, self).__init__()
        #: The active Shell
        self.shell = shell
        #: The :class:`~pypsi.cmdline.CommandInvocation` to execute.
        self.invoke = invoke
        #: Exception info, as returned by :meth:`sys.exc_info` if an exception occurred.
        self.exc_info = None
        #: The invocation return code.
        self.rc = None

        if stdin:
            self.invoke.stdin = stdin
        if stdout:
            self.invoke.stdout = stdout
        if stderr:
            self.invoke.stderr = stderr

    def run(self):
        '''
        Run the command invocation.
        '''

        try:
            self.rc = self.invoke(self.shell)
        except:
            self.exc_info = sys.exc_info()
            self.rc = None
        finally:
            pass

    def stop(self):
        '''
        Attempt to stop the thread by explitily closing the stdin, stdout, and
        stderr streams.
        '''

        if self.is_alive():
            try:
                self.invoke.close_streams()
            except:
                pass
