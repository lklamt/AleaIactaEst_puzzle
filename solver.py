import numpy as np
import json
import itertools
import logging
import os

from pprint import pformat
from scipy import ndimage


class solver:
    """
    Class to solve the Alea Iacta Est Riddle
    (https://www.knobelbox.com/geduldsspiele/jean-claude-constantin/legepuzzle/5743/alea-iacta-est)

    The riddle works as follow:
    The board is a square of 7x7 squares. Each Square is filled with a number from 1 to 6 (each 7 times present);
    7 squares are left empty (board layout can be found under "INPUT/board.json"; emtpy fields --> 0).
    Additionally, the game consists of a set of tiles.
    Each tile can be found under "Input/tiles.json" (1 -> part of tile).

    The player first rolls 6 dices. The player then tries to assemble the 6 dices on fields with the corresponding
    number while filling all other fields of the board with the tiles.
    Finally, only a single field without a number has to be left empty.

    The vendor claims all combinations of dices have a solution.
    In contrast, this solver does not find a solution when the dice shows six times the "2".

    The solver works in two steps:
    Firstly, it creates a list of all combinations for the given combinations of dices, while simultanouesly adding
    all combinations for the left over empty field.

    Secondly, based on this list of possible combinations for the dices, the solver recursively tries to add one tile
    after another while complying to no collisions and not leaving single fields free and "isolated".

    Due to the vast amount of combinations in step 1 for certain combinations of dices the solver will likely not
    converge. For Example for the combination 1,2,3,4,5,6 on the dices we will have 7^7 = 823543 start combinations.
    For other combinations like 6,6,6,6,6,6 we have much less combinations to place the dices (+empty field)
    on the board (49). For these cases the algorithm will find all possible solutions within a few minutes.

    Thus, one can define a break criterion when running step two by defining after how many solutions the
    algorithm shall stop.
    """
    def __init__(self,
                 logger,
                 board_file_name: str="Input/board.json",
                 tiles_file_name: str="Input/tiles.json"):
        """
        Initializer for solver loads the board and tiles, sorts them by size
        :param logger: Logger to log to console
        :param board_file_name: Filename to load board from
        :param tiles_file_name: Filename to load tiles from
        """
        self.logger = logger

        # Opening JSON file for tiles
        self.tiles = self.__load_shapes_from_json__(tiles_file_name)
        self.board = self.__load_shapes_from_json__(board_file_name)

        # initialize list for solutions found
        self.solutions_found = []

    def __load_shapes_from_json__(self,
                              file_name: str) -> dict:
        """
        Load dictionary of shapes (2D-arrays) from file_name
        :param file_name: file_name to load shapes from
        :return: dictionary containing the shapes and names
        """
        # Opening JSON file
        f = open(file_name)
        shapes = json.load(f)
        # Transform to numpy array
        for key in shapes:
            shapes[key] = np.array(shapes[key])
        return shapes

    def create_dice_combs(self,
                          dices: list) -> tuple:
        """
        Function to create list of all possible combinations on how to place dices and empty field on the board.
        :param dices: list of the combinations of dices
        :return: 2 lists of possible board combinations.
            The first list contains 2D-arrays (boards) having the fields flagged (1 vs 0), which are blocked by dice or
            empty field.
            The second list contains 2D-arrays (boards) containing field content from dices and emty fields
        """
        self.logger.info("Creating combinations of dice positions on board")
        # create two empty boards position
        # blocked_field will be used to save list of boards whether field is empty or not (1 vs 0) starting with empty
        # board
        blocked_field = [np.zeros(self.board["board"].shape)]
        # blocked_field_content will be used to save list of boards what field if filled with starting with empty board
        blocked_field_content = [np.zeros(self.board["board"].shape)]

        # add empty field to list of dice
        self.dices = np.append(dices, np.array([0]))

        # Iterate over each number present in the list of dices
        for number in np.unique(self.dices):
            # how many fields on board have number
            n_number = np.count_nonzero((self.board["board"] == number))
            # list of all combinations to place the number of dices with number on fields with number
            combs = list(itertools.combinations(range(n_number), np.count_nonzero((np.array(self.dices) == number))))
            # create board with fields equal number set to 0 .. n_number-1 all other set to -1
            board_with_number_only = np.ones(self.board["board"].shape) * (-1)
            board_with_number_only[(self.board["board"] == number)] = range(n_number)

            # saving content from blocked_field and blocked_field_content to temp lists and emptying lists
            temp_blocked_field = blocked_field.copy()
            blocked_field = []
            temp_blocked_field_content = blocked_field_content.copy()
            blocked_field_content = []

            # Iterating over all combinations and combining them with the combinations from previous iterations
            for i in combs:
                # Filling empty board for this combination
                empty_board = np.zeros(self.board["board"].shape)
                empty_board[np.isin(board_with_number_only, i)] = 1
                # adding new combination to all other existing boards from previous iterations
                blocked_field += [j + empty_board for j in temp_blocked_field]
                blocked_field_content += [j + empty_board * number for j in temp_blocked_field_content]

        self.blocked_field = blocked_field
        self.blocked_field_content = blocked_field_content
        return self.blocked_field, self.blocked_field_content

    def __sum_adjacent_fields__(self,
                                field: np.ndarray) -> tuple:
        """
        Function to sum the adjacent fields (non-diagonal adjacent). It is used to judge, whether a single free field is
        entirely circled by blocked fields and then stop early.
        :param array: 2D numpy array reflecting the current field status (1 for blocked, 0 for free)
        :return: Tuple of 2D numpy arrays of same shape as input field;
            First numpy array reflects the sum of adjacent fields
            Second numpy array reflects whether the field is used or not
        """
        # Create a convolution kernel with all ones except for the center element, which is set to zero
        kernel = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])

        # Define inverse kernel to check whether field is used (for single field actually quite useless)
        inverse_kernel = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]])

        # Calculate the sum of the adjacent fields by applying the convolution kernel to the input array
        output = ndimage.convolve(field, kernel, mode='constant', cval=1)
        inverse_output = ndimage.convolve(field, inverse_kernel, mode='constant', cval=1)

        return output, inverse_output

    def __add_tile__(self,
                     blocked_field_i: np.ndarray,
                     blocked_field_content_i: np.ndarray,
                     tiles_keys_left: list,
                     tiles_shapes_left: list,
                     break_criterion: int) -> None:
        """
        Function called recursively to add new tile to board while checking constraints. If constraints are not
        fulfilled the function returns.
        If all tiles have been placed, the function adds solution to list of solutions.
        The function checks the following constraints:
        - Tile does not colide with tile already placed
        - Tile does not leave single isolated field free while no such single field tile left

        The function iterates over all possible positions for tile on board including rotations while using symmetries.
        :param blocked_field: 2D numpy array current status (1 vs 0) whether blocked
        :param blocked_field_content: 2D numpy array current status (1 vs 0) with current content
        :param tiles_names_left: all names of tiles left
        :param tiles_shapes_left: all shapes of tiles left to be placed
        :param break_criterion: How many solutions to search for bevor breaking
        :return: None
        """
        # check if break_criterion is fulfilled
        if len(self.solutions_found) >= break_criterion:
            return
        # check if no tiles left --> solution found
        if tiles_keys_left != []:
            # check if all single isolated fields are left --> return to previous level
            sum_adjacent, inverse_adjacent = self.__sum_adjacent_fields__(blocked_field_i)
            # ein einzelnes leeres Feld übrig
            if (sum_adjacent[inverse_adjacent == 0] == self.compare_adjacent[inverse_adjacent == 0]).any()\
                    and (np.min([len(x[x == 1]) for x in tiles_shapes_left]) > 1):
                logging.debug("Returning as one empty field solely")
                return

            # pick next tile to place
            tile_picked_shape = tiles_shapes_left.pop()
            tile_picked_key = tiles_keys_left.pop()

            # find all non-symmetric rotations for tile
            tile_picked_rots = [np.rot90(tile_picked_shape, rot) for rot in range(4)]
            L = {array.tostring(): array for array in tile_picked_rots}
            tile_picked_rots = L.values()
            # iterate over rotation
            for tile_picked_rot in tile_picked_rots:
                # iterate over possible possitions
                # x_off and y_off are the positions where to place left top corner of tile
                for x_off in range(blocked_field_i.shape[0] - tile_picked_rot.shape[0] + 1):
                    for y_off in range(blocked_field_i.shape[1] - tile_picked_rot.shape[1] + 1):
                        # extract area affected by tile from board and add to tile
                        area_to_compare = blocked_field_i[x_off:x_off + tile_picked_rot.shape[0],
                                          y_off:y_off + tile_picked_rot.shape[1]] + tile_picked_rot
                        # check if collision
                        if not (area_to_compare > 1).any():
                            blocked_field_i[x_off:x_off + tile_picked_rot.shape[0],
                            y_off:y_off + tile_picked_rot.shape[1]] = area_to_compare
                            blocked_field_content_i[x_off:x_off + tile_picked_rot.shape[0],
                            y_off:y_off + tile_picked_rot.shape[1]] += list(tile_picked_rot * tile_picked_key)
                            self.__add_tile__(
                                blocked_field_i, blocked_field_content_i, tiles_keys_left, tiles_shapes_left,
                                break_criterion)
                            blocked_field_i[x_off:x_off + tile_picked_rot.shape[0],
                            y_off:y_off + tile_picked_rot.shape[1]] -= tile_picked_rot
                            blocked_field_content_i[x_off:x_off + tile_picked_rot.shape[0],
                            y_off:y_off + tile_picked_rot.shape[1]] -= tile_picked_rot * tile_picked_key
                        else:
                            # case of collision with used field
                            continue
            # add tiles to list of tiles again
            tiles_shapes_left.append(tile_picked_shape)
            tiles_keys_left.append(tile_picked_key)
        else:
            if len(blocked_field_i[blocked_field_i == 0]) == 0:
                self.solutions_found.append(blocked_field_content_i.copy())
                self.logger.info(f"Found Solution NR {len(self.solutions_found)}")
                pretty_sol = self.__translate_solution__(blocked_field_content_i)
                for line in pformat(pretty_sol).split('\n'):
                    self.logger.info(line)
                try:
                    os.mkdir(f"Result/{''.join([str(int(x)) for x in self.dices[:-1]])}")
                except:
                    pass
                with open(f"Result/{''.join([str(int(x)) for x in self.dices[:-1]])}/"
                          f"Solution_{str(len(self.solutions_found))}.txt", 'w') \
                        as file:
                    for row in pretty_sol:
                        file.write(' '.join([str(a) for a in row]) + '\n')
            return

    def __translate_solution__(self, solution: np.ndarray):
        """
        Function to map tiles names and keys in solutions
        :param solution: solution with numbers for tiles due to np-datatype
        :return: mapped solution as 2D python array with name of shape mapped
        """
        # translate solutions
        temp_sol = list(solution)
        temp_sol = [list(x) for x in temp_sol]
        for j, k in zip(self.tiles_names, self.tiles_names_keys):
            for idxs, s in enumerate(temp_sol):
                temp_sol[idxs] = [j if x == k else x if type(x) == str else int(x) for x in s]
        for idxs, s in enumerate(temp_sol):
            temp_sol[idxs] = [str(x) for x in s]
        return temp_sol

    def place_tiles(self, break_criterion: int = 50):
        """
        This function calls __add_tile__ recursively to place the tiles
        For faster convergence it first sorts the tiles by name.
        :param break_criterion: How many solutions to search for bevor breaking
        :return: None
        """
        self.logger.info("Adding tiles to boards")
        # sort tiles from small to large for faster convergence starting allocation with largest tiles (in area metric)
        tiles_list = list(self.tiles.items())
        self.tiles_list = sorted(tiles_list, key=lambda data: data[1].shape[0] * data[1].shape[0])
        self.tiles_shapes = [x[1] for x in tiles_list]
        self.tiles_names = [x[0] for x in tiles_list]
        # create array of numeric keys for tiles due to faster processing on numpy arrays
        self.tiles_names_keys = [100 + x for x in list(range(len(self.tiles_names)))]

        # sum of all adjacent field if all are used
        # Calculate how many fields are adjacent to given field
        self.compare_adjacent, __ = self.__sum_adjacent_fields__(np.ones(self.board["board"].shape))

        for i in range(len(self.blocked_field)):
            self.__add_tile__(np.array(self.blocked_field[i]), np.array(self.blocked_field_content[i]),
                              self.tiles_names_keys.copy(), self.tiles_shapes, break_criterion)
            if len(self.solutions_found) >= break_criterion:
                self.logger.info(f"Exited after finding {len(self.solutions_found)} solutions")
                break
        self.solutions_mapped = []
        for i in self.solutions_found:
            self.solutions_mapped.append(self.__translate_solution__(i))

        return self.solutions_mapped