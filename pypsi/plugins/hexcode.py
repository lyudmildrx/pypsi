
from pypsi.base import Plugin
from pypsi.cmdline import StringToken


class HexCodePlugin(Plugin):

    def __init__(self, preprocess=5, **kwargs):
        super(HexCodePlugin, self).__init__(preprocess=preprocess, **kwargs)

    def on_tokenize(self, shell, tokens, origin):
        for token in tokens:
            if not isinstance(token, StringToken) or '\\' not in token.text:
                continue

            escape = False
            hexcode = None
            text = ''
            for c in token.text:
                if escape:
                    escape = False
                    if c == 'x':
                        hexcode = ''
                    else:
                        text += '\\' + c
                elif hexcode is not None:
                    hexcode += c
                    if len(hexcode) == 2:
                        try:
                            hexcode = int(hexcode, base=16)
                            text += chr(hexcode)
                            hexcode = None
                        except ValueError:
                            text += '\\x' + hexcode
                elif c == '\\':
                    escape = True
                else:
                    text += c

            if hexcode:
                text += '\\x' + hexcode

            if escape:
                text += '\\'

            token.text = text
        return tokens