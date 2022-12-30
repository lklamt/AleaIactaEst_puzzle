"""
This solver solves the puzzle alea iacta est from Knobelbox
(https://www.knobelbox.com/geduldsspiele/jean-claude-constantin/legepuzzle/5743/alea-iacta-est)
"""

import numpy as np
import logging
import solver
import sys

logger = logging.getLogger('puzzle_logger')
logger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s – %(name)s – %(levelname)s:%(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)
logger.propagate = False

if __name__ == "__main__":
    # Handle user input and convert to list
    inp = [int(x) for x in sys.argv[1:]]
    dices = np.array(inp)

    solv = solver.solver(logger)
    solv.create_dice_combs(dices)
    solv.place_tiles(break_criterion=10)


