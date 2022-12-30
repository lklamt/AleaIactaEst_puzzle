# Puzzle Solver Alea Iacta Est

## The riddle

The riddle works as follow:
The board is a square of 7x7 squares. Each Square is filled with a number from 1 to 6 (each 7 times present);
7 squares are left empty (board layout can be found under `Input/board.json`; emtpy fields --> 0).
Additionally, the game consists of a set of tiles.
Each tile can be found under `Input/tiles.json` (1 -> part of tile).

The player first rolls 6 dices. The player then tries to assemble the 6 dices on fields with the corresponding
number while filling all other fields of the board with the tiles.
Finally, only a single field without a number has to be left empty.

The vendor claims all combinations of dice have a solution.
In contrast, this solver does not find a solution when the dice shows six times the "2".
<br><br>

##### Reference:
https://www.knobelbox.com/geduldsspiele/jean-claude-constantin/legepuzzle/5743/alea-iacta-est

## The solver
The solver works in two steps:
Firstly, it creates a list of all combinations for the given combinations of dices, while simultanouesly adding
all combinations for the left over empty field.
<br><br>
Secondly, based on this list of possible combinations for the dices, the solver recursively tries to add one tile
after another while complying to no collisions and not leaving single fields free and "isolated".
<br>
Due to the vast amount of combinations in step 1 for certain combinations of dices the solver will likely not
converge. For Example for the combination 1,2,3,4,5,6 on the dices we will have 7^7 = 823543 start combinations.
For other combinations like 6,6,6,6,6,6 we have much less combinations to place the dices (+empty field)
on the board (49). For these cases the algorithm will find all possible solutions within a few minutes.
<br>
Thus, one can define a break criterion when running step two by defining after how many solutions the
algorithm shall stop.

### Input
The solver uses the files `input/board.json` and `input/tiles.json` as input. In case a non-standard board shall be used,
please change these files.
<br>
Furthermore, the solver gets the n command line parameters, where n is the number of dices.
Each input parameter corresponds to a result of a dice.
For the result of the 6 dices being all 6 we, thus, start the solver by
```
main.py 6 6 6 6 6 6
```

### Results
The logger will output all results to the command line as a matrix.
The numbers in the matrix reflect the numbers from the dices ('0' is the empty field).
The letters in the matrix reflect the tile used.
```
30/12/2022 11:58:29 PM – puzzle_logger – INFO:Creating combinations of dice positions on board
30/12/2022 11:58:29 PM – puzzle_logger – INFO:Adding tiles to boards
30/12/2022 11:58:29 PM – puzzle_logger – INFO:Found Solution NR 1
30/12/2022 11:58:29 PM – puzzle_logger – INFO:[['b', 'b', 'h', 'h', '6', '0', 'c'],
30/12/2022 11:58:29 PM – puzzle_logger – INFO: ['b', 'b', '6', 'h', 'h', 'i', 'c'],
30/12/2022 11:58:29 PM – puzzle_logger – INFO: ['b', '6', 'd', 'd', 'h', 'i', 'c'],
30/12/2022 11:58:29 PM – puzzle_logger – INFO: ['a', 'a', 'd', '6', 'e', 'i', 'i'],
30/12/2022 11:58:29 PM – puzzle_logger – INFO: ['a', 'd', 'd', 'e', 'e', '6', 'i'],
30/12/2022 11:58:29 PM – puzzle_logger – INFO: ['a', 'a', 'g', 'f', 'e', 'e', '6'],
30/12/2022 11:58:29 PM – puzzle_logger – INFO: ['g', 'g', 'g', 'f', 'f', 'f', 'f']]
```
The result is also saved to the files `Result/<dice_combination>/Solution_<n>.txt`.
Exemplary results can be found in `Result/666666/Solution_1.txt`.

## Contributors
Lukas Klamt, Dec 2022