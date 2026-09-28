import logging
import sys

import click

OK = 25
logging.addLevelName(OK, 'OK')

# Solarized Dark, as truecolor: base01, green, yellow, red.
PALETTE = {
    logging.INFO:    (88, 110, 117),
    OK:              (133, 153, 0),
    logging.WARNING: (181, 137, 0),
    logging.ERROR:   (220, 50, 47),
}


class Formatter(logging.Formatter):

    def __init__(self, color: bool):
        super().__init__('%(message)s')
        self.color = color

    def format(self, record) -> str:
        text = super().format(record)

        return click.style(text, fg=PALETTE[record.levelno]) if self.color else text


def log_setup(color: bool) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(Formatter(color))

    logger = logging.getLogger('suil')
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
