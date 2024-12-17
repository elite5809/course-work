/** main.h
* ===========================================================
* Project: Final Project
* ===========================================================
*/

#ifndef MAIN_H
#define MAIN_H

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <time.h>
#include <string.h>
#include "C:\PDCurses-3.9\curses.h"

typedef struct PlayerStruct{
    char name[21];
    bool alive;
    char direction;
    char oldDirection;
    int x;
    int y;
} Player;

/**
 * @brief Initializes srand for rand, establishes default names file if it doesnt exist, implements ncurses settings
 */
void initProgram();

/**
 * @brief Initializes colors and color pairs in ncurses
 */
void initColors();

/**
 * @brief Handles the menu loop
 */
void menuHandler();

/**
 * @brief Displays and refreshes the menu while highlighting the selected option
 * @param menu Menu option index to highlight
 */
void displayMenu(int menu);

/**
 * @brief Handles the user inputs for the menu system
 * @param menu Current menu index selection
 * @return Changed menu index selection
 */
int menuInput(int menu);

/**
 * @brief Displays help menu
 */
void showHelp();

/**
 * @brief Displays and handles the names menu for changing the names of each player
 */
void showNames();

/**
 * @brief Loads names from the name file into the names parameter
 * @param names Array of names that gets updated with the data in the names file
 */
void loadNames(char** names);

/**
 * @brief Saves names from the names parameter into the names file
 * @param names Array of names that overwrites the data in the names file
 */
void saveNames(char** names);

/**
 * @brief Initializes game windows and game variables like gameArena and players
 * @param gameArena Holds the arena grid and what coords are not available
 * @param players Holds information regarding the players
 */
void initGame(char** gameArena, Player* players);

/**
 * @brief Grabs keyboard inputs and processes them by adjusting the respective players direction
 * @param players Holds information regarding the players
 * @return Returns 0 or 1 whether a quit button (escape or backspace) was pressed
 */
int playerInput(Player* players);

/**
 * @brief Handles the algorithm for determining were the bot players go
 * @param gameArena Holds the arena grid and what coords are not available
 * @param players Holds information regarding the players
 */
void computerInput(char** gameArena, Player* players, int i);

/**
 * @brief Updates the position of the players and the gameArena with information about where players cannot go anymore
 * @param gameArena Holds the arena grid and what coords are not available
 * @param players Holds information regarding the players
 */
void updateMoves(char** gameArena, Player* players);

/**
 * @brief Checks if players have crashed into something according to the information in gameArena
 * @param gameArena Holds the arena grid and what coords are not available
 * @param players Holds information regarding the players
 */
void checkCollisions(char** gameArena, Player* players);

/**
 * @brief Deletes the color that was killed from the screen and updates gameArena by clearing those areas as available
 * @param gameArena Holds the arena grid and what coords are not available
 * @param player Player index to kill (Color pairs use this number plus 1 to erase correct color)
 */
void killColor(char** gameArena, int player);

/**
 * @brief Updates screen with new information from the players struct
 * @param players Holds information regarding the players
 */
void updateScreen(Player* players);

/**
 * @brief Counts how many players died and checks if someone one or if there was a tie
 * @param players Holds information regarding the players
 * @return 
 */
int checkWinner(Player* players);

/**
 * @brief Displays a game ending message of a player winning or a tie. It also allows for users to quit to menu or close the pogram.
 * @param players Holds information regarding the players
 * @param win Which end state determined by checkWinner() (0 - tie; 1-4 - player number that won)
 */
void endGame(Player* players, int win);

/**
 * @brief Clears the memory from the pointers used in the game
 * @param gameArena Holds the arena grid and what coords are not available
 * @param players Holds information regarding the players
 */
void clearMem(char** gameArena, Player* players);

#endif //MAIN_H