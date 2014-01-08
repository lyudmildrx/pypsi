
from pypsi.base import Command, PypsiArgParser
import argparse

EchoCmdUsage = "%(prog)s [-hewi] [-n] [-h] message"


class EchoCommand(Command):

    def __init__(self, name='echo', topic='shell', **kwargs):
        self.parser = PypsiArgParser(
            prog=name,
            description='display a line of text',
            usage=EchoCmdUsage
        )

        subcmd = self.parser.add_argument_group(title='Stream')
        subcmd.add_argument(
            '-e', '--error', help='print to error stream', action='store_true'
        )
        subcmd.add_argument(
            '-i', '--info', help='print to info stream', action='store_true'
        )
        subcmd.add_argument(
            '-w', '--warn', help='print to warn stream', action='store_true'
        )

        self.parser.add_argument(
            'message', help='message to print', nargs=argparse.REMAINDER
        )

        self.parser.add_argument(
            '-n', '--nolf', help="don't print newline character", action='store_true'
        )

        super(EchoCommand, self).__init__(name=name, usage=self.parser.format_help(), topic=topic, brief='print a line of text', **kwargs)

    def run(self, shell, args, ctx):
        ns = self.parser.parse_args(shell, args)
        if self.parser.rc is not None:
            return self.parser.rc

        fn = shell.info
        if ns.error:
            fn = shell.error
        elif ns.warn:
            fn = shell.warn

        tail = '' if ns.nolf else '\n'

        fn.write(' '.join(ns.message), tail)

        return 0