# -*- coding: utf-8 -*-
import asyncio
import logging
import sys

import config
import listener
import tts

logger = logging.getLogger(__name__)


async def main():
    if not init():
        return 1
    await run()
    return 0


def init():
    init_logging()
    config.init()

    if not tts.init():
        return False
    listener.init()
    return True


def init_logging():
    logging.basicConfig(
        format='{asctime} {levelname} [{name}]: {message}',
        style='{',
        level=logging.INFO,
    )


async def run():
    logger.info('Running event loop')
    await asyncio.Event().wait()


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
