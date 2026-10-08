import logging
import sys
import textwrap

import click

OK = 25
INDENT = ' ' * 4

# Solarized Dark, as truecolor: base01, green, yellow, red.
PALETTE = {
    logging.INFO:    (88, 110, 117),
    OK:              (133, 153, 0),
    logging.WARNING: (181, 137, 0),
    logging.ERROR:   (220, 50, 47),
}


class Formatter(logging.Formatter):

    def __init__(self, color: bool):
        super().__init__('[%(levelname)s]: %(message)s')
        self.color = color

    def formatMessage(self, record) -> str:
        first, _, rest = super().formatMessage(record).partition('\n')
        text = first + ('\n' + textwrap.indent(rest, INDENT) if rest else '')

        return click.style(text, fg=PALETTE[record.levelno]) if self.color else text

    def formatException(self, exc_info) -> str:
        return textwrap.indent(super().formatException(exc_info), INDENT)


def log_setup(color: bool) -> None:
    logging.addLevelName(OK, 'ok')

    for level in (logging.INFO, logging.WARNING, logging.ERROR):
        logging.addLevelName(level, logging.getLevelName(level).lower())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(Formatter(color))

    logger = logging.getLogger('suil')
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
