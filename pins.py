#!/usr/bin/env python3

# ==============================================================================
#
#          FILE:  pins.py
#
#         USAGE:  ./pins.py
#
#   DESCRIPTION:  A command-line implementation of the game of Pins, a variant
#                 of the game of Nim. A human player competes against a CPU
#                 opponent with multiple difficulty levels.
#
#       OPTIONS:  ---
#  REQUIREMENTS:  ---
#          BUGS:  ---
#         NOTES:  ---
#        AUTHOR:  FNGarvin (184324400+FNGarvin@users.noreply.github.com)
#       CREATED:  2025-06-15
#      REVISION:  1.0
#
# ==============================================================================

import os
import sys
import random
import functools

# --- Game Configuration ---
INITIAL_ROWS = [3, 5, 7]
PIN_SYMBOL = "│"
EMPTY_SYMBOL = " "

# --- Game AI Logic ---

def get_all_possible_moves(board_state):
    """Generates all valid moves from the current board state."""
    moves = []
    for row_idx, row in enumerate(board_state):
        for block_idx, block_size in enumerate(row):
            # A move is defined by (row_idx, block_idx, start, count)
            # where 'start' is the 0-indexed pin to start removing from
            # and 'count' is the number of pins to remove.
            for count in range(1, block_size + 1):
                for start in range(block_size - count + 1):
                    moves.append((row_idx, block_idx, start, count))
    return moves

def apply_move(board_state, move):
    """Applies a move to a copy of the board state and returns the new state."""
    row_idx, block_idx, start, count = move
    new_board = [list(row) for row in board_state]
    
    block_size = new_board[row_idx][block_idx]
    
    # Remove the block that is being modified
    del new_board[row_idx][block_idx]

    # Calculate the sizes of the new blocks to be added
    left_block_size = start
    right_block_size = block_size - (start + count)

    if left_block_size > 0:
        new_board[row_idx].append(left_block_size)
    if right_block_size > 0:
        new_board[row_idx].append(right_block_size)
    
    # Sort blocks within the row for consistent representation
    for row in new_board:
        row.sort()

    # Filter out empty rows
    return [row for row in new_board if row]


def get_nim_sum(board_state):
    """Calculates the Nim-sum of the board state."""
    all_blocks = [block for row in board_state for block in row]
    if not all_blocks:
        return 0
    return functools.reduce(lambda x, y: x ^ y, all_blocks)

def expert_ai_move(board_state):
    """Calculates a perfect move using Nim theory."""
    all_moves = get_all_possible_moves(board_state)
    random.shuffle(all_moves) # Introduce variety in move choice

    current_nim_sum = get_nim_sum(board_state)

    # Misere play endgame logic
    all_blocks = [block for row in board_state for block in row]
    is_endgame = all(block_size == 1 for block_size in all_blocks)

    if is_endgame:
        # If all heaps are size 1, the goal is to leave an odd number of heaps
        return all_moves[0] # Just take one heap

    # Standard Nim strategy
    for move in all_moves:
        next_state = apply_move(board_state, move)
        # Check if the move leads to a state where all heaps would be size 1
        all_next_blocks = [block for row in next_state for block in row]
        is_next_state_endgame = all(block_size == 1 for block_size in all_next_blocks)
        
        target_nim_sum = 0
        # If the move leads to the endgame, we must adjust our target
        if is_next_state_endgame:
            # We want to leave an ODD number of heaps for the opponent
            if len(all_next_blocks) % 2 == 0:
                # This move leaves an even number of heaps, which is a losing misere position
                # so we should avoid it if the current nim_sum is the target
                if current_nim_sum == get_nim_sum(board_state) ^ get_nim_sum(next_state):
                    continue
            # If it leaves an odd number, that's a winning misere move.
            else: 
                return move
        
        # Normal play: find a move that results in a Nim-sum of 0
        if get_nim_sum(next_state) == 0:
            return move

    # If no winning move is found (i.e., we are in a losing position), make a random move.
    return random.choice(all_moves)

def intermediate_ai_move(board_state):
    """A mix of expert and random moves."""
    if random.random() < 0.6: # 60% chance of playing optimally
        return expert_ai_move(board_state)
    return random.choice(get_all_possible_moves(board_state))

def novice_ai_move(board_state):
    """A completely random valid move."""
    return random.choice(get_all_possible_moves(board_state))

# --- UI and Game Loop ---

def print_board(board_state):
    """Prints the current state of the board to the console."""
    print("\n" + "=" * 20)
    max_pins = max(INITIAL_ROWS)
    all_current_pins = [sum(row) for row in board_state]
    initial_lookup = {size: i for i, size in enumerate(INITIAL_ROWS)}
    
    drawn_rows = set()

    # Draw rows that still exist
    for row_idx, row in enumerate(board_state):
        original_size = sum(row)
        # This logic is imperfect if multiple rows start with the same count
        # For 3, 5, 7 it is fine.
        original_row_idx = initial_lookup.get(original_size, row_idx)

        pins_to_draw = board_state[row_idx]
            
        temp_row_str = "  ".join([PIN_SYMBOL * p for p in pins_to_draw])
        padding = " " * ((max_pins * 2 - len(temp_row_str)) // 2)

        print(f"Row {row_idx + 1}: {padding}{temp_row_str}")
        drawn_rows.add(original_size)

    # Account for completely removed rows
    for r_size in INITIAL_ROWS:
        if r_size not in drawn_rows and r_size not in all_current_pins:
             print(f"Row {initial_lookup[r_size]+1}: <empty>")


    print("=" * 20 + "\n")

def get_player_move(board_state):
    """Prompts the human player for a move and validates it."""
    while True:
        try:
            # Get input for row
            row_input = int(input(f"Enter row to take from (1-{len(board_state)}): "))
            row_idx = row_input - 1
            if not (0 <= row_idx < len(board_state) and board_state[row_idx]):
                print("Invalid row. Please try again.")
                continue

            # Display the blocks in the selected row
            row_blocks = board_state[row_idx]
            print(f"Row {row_input} has blocks of sizes: {row_blocks}")
            
            # Get input for block
            block_idx = 0
            if len(row_blocks) > 1:
                block_input = int(input(f"Which size block to take from? (e.g., {row_blocks[0]}): "))
                if block_input not in row_blocks:
                    print("Invalid block size. Please try again.")
                    continue
                block_idx = row_blocks.index(block_input)
            else:
                block_input = row_blocks[0]

            # Get input for count
            count = int(input(f"How many pins to take from the block of {block_input}? "))
            if not (1 <= count <= block_input):
                 print(f"You must take between 1 and {block_input} pins.")
                 continue

            # Get input for start position
            start = 0
            if count < block_input:
                start_input = int(input(f"From where? (1=left, 2=right, 3=middle): "))
                if start_input == 1: # Left
                    start = 0
                elif start_input == 2: # Right
                    start = block_input - count
                elif start_input == 3: # Middle
                    # Taking from the middle is only unambiguous if the remainder is even
                    if (block_input - count) % 2 != 0:
                        print("Cannot take from middle and leave two equal sides. Try again.")
                        continue
                    start = (block_input - count) // 2
                else:
                    print("Invalid position. Please try again.")
                    continue
            
            return (row_idx, block_idx, start, count)

        except (ValueError, IndexError):
            print("Invalid input. Please enter numbers only.")
        except Exception as e:
            print(f"An error occurred: {e}")

def main():
    """Main function to run the game."""
    program_name = os.path.basename(sys.argv[0])
    print(f"Welcome to the Game of Pins!")
    print("The player who is forced to take the last pin loses.")
    
    # Choose difficulty
    while True:
        difficulty = input("Choose difficulty (1: Novice, 2: Intermediate, 3: Expert): ")
        if difficulty in ["1", "2", "3"]:
            break
        print("Invalid choice. Please enter 1, 2, or 3.")

    ai_functions = {
        "1": novice_ai_move,
        "2": intermediate_ai_move,
        "3": expert_ai_move
    }
    ai_move_func = ai_functions[difficulty]
    
    # Initial board state: each row is a list containing one block
    board = [[size] for size in INITIAL_ROWS]
    
    # Randomly decide who goes first
    turn = random.choice(['player', 'cpu'])
    print(f"\n{turn.capitalize()} will go first.")
    
    while True:
        if not get_all_possible_moves(board):
            winner = "CPU" if turn == 'player' else "Player"
            print(f"All pins are gone! {winner} wins!")
            break

        print_board(board)

        if turn == 'player':
            print("Your turn.")
            move = get_player_move(board)
            board = apply_move(board, move)
            turn = 'cpu'
        else:
            print("CPU's turn...")
            move = ai_move_func(board)
            board = apply_move(board, move)
            print("CPU has made its move.")
            turn = 'player'

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame exited. Goodbye!")
    except Exception as e:
        print(f"\nA critical error occurred: {e}")

#END OF pins.py
