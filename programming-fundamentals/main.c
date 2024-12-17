/** main.c
* ===========================================================
* Project: Final Project
* ===========================================================
*/

#include "main.h"

//Program Variables
const char* filename = "./tronNames.txt";
bool quit = 0;

//Window pointers
WINDOW* arenaWin;
WINDOW* statusWin;

//Game settings
int numPlayers = 2;
bool twoHuman = false;

int main(){
    initProgram();

    //Runtime
    do{
        menuHandler(); //Menu loop

        //Game initialize
        char** gameArena = (char**)malloc(sizeof(char*) * 25);
        for (int i = 0; i < 25; i++) gameArena[i] = (char*)malloc(120);
        Player* players = (Player*)malloc(sizeof(Player) * numPlayers);
        initGame(gameArena, players);
        int win = -1;

        //Game runtime
        do{
            napms(50);
            if (playerInput(players)) break;
            for (int i = (twoHuman + 1); i < numPlayers; i++) computerInput(gameArena, players, i);
            updateMoves(gameArena, players);
            checkCollisions(gameArena, players);
            updateScreen(players);
            win = checkWinner(players);
        }
        while (win == -1);
        //End game handler
        if (win != -1) endGame(players, win);
        clearMem(gameArena, players);
    }
    while(!quit);

    endwin();
    return 0;
}

void initProgram(){
    //Initialize random
    srand((unsigned int)time(0));

    //Establish default namesFile if no file found
    FILE* namesFile = fopen(filename, "rb");
    if (namesFile == NULL){
        char** names = (char**)malloc(sizeof(char*) * 4);
        for (int i = 0; i < 4; i++){
            names[i] = (char*)malloc(21);
            sprintf(names[i], "Player %d", i + 1);
        }
        saveNames(names);
        for (int i = 0; i < 4; i++) free(names[i]);
        free(names);
    }
    else fclose(namesFile);

    //Initialize ncurses settings
    initscr();
    nodelay(stdscr, true);
    keypad(stdscr, true);
    curs_set(false);
    noecho();
    start_color();
    initColors();
    refresh();
}

void initColors(){
    init_color(COLOR_BLUE, 250, 250, 999);
    init_color(COLOR_RED, 999, 0, 0);
    init_color(COLOR_GREEN, 0, 999, 0);
    init_color(COLOR_YELLOW, 999, 999, 0);
    init_color(8, 375, 375, 375);

    init_pair(1, COLOR_BLUE, COLOR_BLACK);
    init_pair(2, COLOR_RED, COLOR_BLACK);
    init_pair(3, COLOR_GREEN, COLOR_BLACK);
    init_pair(4, COLOR_YELLOW, COLOR_BLACK);
    init_pair(5, 8, COLOR_BLACK);
    init_pair(6, COLOR_BLACK, COLOR_WHITE);
}

void menuHandler(){
    int menu = 0;

    while (menu != -1){
        displayMenu(menu);
        menu = menuInput(menu);
    }
}

void displayMenu(int menu){
    mvprintw(0, 20,  "|------------------||----------------\\  |------------------||-------\\     |----|\n");
    mvprintw(1, 20,  "|                  ||                 | |                  ||        \\    |    |\n");
    mvprintw(2, 20,  "|                  ||     |---|       | |    |--------|    ||         \\   |    |\n");
    mvprintw(3, 20,  "|------      ------||     |   |       | |    |        |    ||    |     \\  |    |\n");
    mvprintw(4, 20,  "      |      |      |     |---|      /  |    |        |    ||    |\\     \\ |    |");
    mvprintw(5, 20,  "      |      |      |               |   |    |        |    ||    | \\     \\|    |");
    mvprintw(6, 20,  "      |      |      |     |---\\      \\  |    |        |    ||    |  \\     |    |");
    mvprintw(7, 20,  "      |      |      |     |    \\      \\ |    |--------|    ||    |   \\         |");
    mvprintw(8, 20,  "      |      |      |     |     \\      \\|                  ||    |    \\        |");
    mvprintw(9, 20,  "      |------|      |-----|      \\-----||------------------||----|     \\-------|");

    if (menu == 0) attron(COLOR_PAIR(6));
    mvprintw(11, 57, "Start");
    attroff(COLOR_PAIR(6));

    if (menu == 1) attron(COLOR_PAIR(6));
    mvprintw(13, 58, "Help");
    attroff(COLOR_PAIR(6));

    if (menu == 2) attron(COLOR_PAIR(6));
    mvprintw(15, 52, "Human Players: %d", twoHuman + 1);
    attroff(COLOR_PAIR(6));

    if (menu == 3) attron(COLOR_PAIR(6));
    mvprintw(17, 53, "Bot Players: %d", numPlayers - (twoHuman + 1));
    attroff(COLOR_PAIR(6));

    if (menu == 4) attron(COLOR_PAIR(6));
    mvprintw(19, 55, "Set names");
    attroff(COLOR_PAIR(6));

    if (menu == 5) attron(COLOR_PAIR(6));
    mvprintw(21, 58, "Exit");
    attroff(COLOR_PAIR(6));

    mvprintw(24, 43, "Press space to execute the command");
    mvprintw(25, 25, "Use W and S or the up and down arrow keys to move up and down the menu");
    mvprintw(26, 27, "Use the A and D or the left and right arrow keys to adjust options");
    mvprintw(27, 45, "Press escape to quit the game");

    refresh();
}

int menuInput(int menu){
    switch(getch()){
            case 'w':
            case KEY_UP:
                if (menu == 0) menu = 6;
                menu--;
                break;
            case 's':
            case KEY_DOWN:
                menu++;
                menu %= 6;
                break;
            case 'a':
            case KEY_LEFT:
                if (menu == 2 && twoHuman && numPlayers > 2){
                    twoHuman = false;
                    numPlayers--;
                }
                else if (menu == 3 && numPlayers > 2) numPlayers--;
                break;
            case 'd':
            case KEY_RIGHT:
                if (menu == 2 && !twoHuman && numPlayers < 4){
                    twoHuman = true;
                    numPlayers++;
                }
                else if (menu == 3 && numPlayers < 4) numPlayers++;
                break;
            case 32:
                switch (menu){
                    case 0:
                        menu--;
                        break;
                    case 1:
                        showHelp();
                        clear();
                        break;
                    case 4:
                        showNames();
                        clear();
                        break;
                    case 5:
                        exit(0);
                        break;
                }
                break;
            case 27:
                endwin();
                exit(0);
                break;
    }
    return menu;
}

void showHelp(){
    clear();
    mvprintw(8, 17, "You and your opponents are in an arena fighting for your lives in a light bike battle!");
    mvprintw(10, 25, "To control your bike in singleplayer mode, use WASD or the arrow keys.");
    mvprintw(12, 15, "In a battle with another user, player 1 will use WASD while player 2 uses the arrow keys.");
    mvprintw(14, 32, "Keep in mind that holding down a key does not help you.");
    mvprintw(15, 34, "You must press down on a key for your bike to turn!");
    mvprintw(17, 29, "At any time, you may press the escape button to close the game");
    mvprintw(18, 34, "or use the backspace button to go back to the menu.");
    mvprintw(20, 47, "Good luck and stay alive!");
    mvprintw(22, 38, "Press any key to go back to the main menu...");
    while (getch() == ERR){}
}

void showNames(){
    clear();
    int opt = 0;
    int c = ' ';
    char** names = (char**)malloc(sizeof(char*) * 4);
    for (int i = 0; i < 4; i++) names[i] = (char*)malloc(21);
    loadNames(names);

    mvprintw(2, 55, "Names menu");
    WINDOW* namesWin = newwin(16, 21, 7, 61);
    while (true){
        if (opt == 0) attron(COLOR_PAIR(6));
        mvprintw(7, 40, "Player 1 (Blue):");
        attroff(COLOR_PAIR(6));

        if (opt == 1) attron(COLOR_PAIR(6));
        mvprintw(12, 40, "Player 2 (Red):");
        attroff(COLOR_PAIR(6));

        if (opt == 2) attron(COLOR_PAIR(6));
        mvprintw(17, 40, "Player 3 (Green):");
        attroff(COLOR_PAIR(6));

        if (opt == 3) attron(COLOR_PAIR(6));
        mvprintw(22, 40, "Player 4 (Yellow):");
        attroff(COLOR_PAIR(6));

        if (opt == 4) attron(COLOR_PAIR(6));
        mvprintw(27, 55, "Exit menu");
        attroff(COLOR_PAIR(6));

        wclear(namesWin);
        mvwprintw(namesWin, 0, 0, "%s", names[0]);
        mvwprintw(namesWin, 5, 0, "%s", names[1]);
        mvwprintw(namesWin, 10, 0, "%s", names[2]);
        mvwprintw(namesWin, 15, 0, "%s", names[3]);

        refresh();
        wrefresh(namesWin);

        c = getch();
        switch (c){
            case KEY_UP:
                if (opt == 0) opt = 5;
                opt--;
                break;
            case KEY_DOWN:
                opt++;
                opt %= 5;
                break;
            case 27:
                exit(0);
            case 32:
                if (opt != 4) break;
                saveNames(names);
                return;
        }

        if (opt == 4) continue;
        unsigned int len = strlen(names[opt]);
        if (c >= 32 && c <= 126 && len != 20){
            names[opt][len] = (char)c;
            names[opt][len + 1] = '\0';
        }
        else if (c == 8 && len != 0) names[opt][len - 1] = '\0';
    }

    for (int i = 0; i < 4; i++) free(names[i]);
    free(names);
}

void loadNames(char** names){
    FILE* file = fopen(filename, "rb");
    for (int i = 0; i < 4; i++) fscanf(file, "%[^\r]\n", names[i]);
    fclose(file);
}

void saveNames(char** names){
    FILE* file = fopen(filename, "w");
    for (int i = 0; i < 4; i++) fprintf(file, "%s\n", names[i]);
    fclose(file);
}

void initGame(char** gameArena, Player* players){
    arenaWin = (WINDOW*)malloc(sizeof(WINDOW));
    statusWin = (WINDOW*)malloc(sizeof(WINDOW));
    
    //Arena initialization
    chtype border = '#' | COLOR_PAIR(5);
    arenaWin = newwin(25, 120, 0, 0);
    refresh();
    for (int y = 0; y < 25; y++){
        for (int x = 0; x < 120; x++){
            if (x == 0 || x == 119 || y == 0 || y == 24) gameArena[y][x] = 'x';
            else gameArena[y][x] = ' ';
            mvwprintw(arenaWin, y, x, " ");
        }
    }
    wborder(arenaWin, border, border, border, border, border, border, border, border);

    //Status board initialization
    statusWin = newwin(5, 120, 25, 0);
    refresh();
    box(statusWin, 0, 0);
    for (int y = 1; y <= 3; y++){
        mvwprintw(statusWin, y, 28, "|");
        mvwprintw(statusWin, y, 29, "|");
        mvwprintw(statusWin, y, 58, "|");
        mvwprintw(statusWin, y, 59, "|");
        mvwprintw(statusWin, y, 88, "|");
        mvwprintw(statusWin, y, 89, "|");
    }

    //Player initialization
    char** names = (char**)malloc(sizeof(char*) * 4);
    for (int i = 0; i < 4; i++) names[i] = (char*)malloc(21);
    loadNames(names);
    
    if (numPlayers == 2){
        players[0].x = 5;
        players[0].y = 12;
        players[1].x = 114;
        players[1].y = 12;
    }
    else{
        players[0].x = 5;
        players[0].y = 8;
        players[1].x = 114;
        players[1].y = 8;
        if (numPlayers == 3){
            players[2].x = 57;
            players[2].y = 15;
        }
        else{
            players[2].x = 5;
            players[2].y = 15;
            players[3].x = 114;
            players[3].y = 15;
        }
    }
    for (int i = 0; i < numPlayers; i++){
        strcpy(players[i].name, names[i]);
        players[i].alive = true;
        players[i].direction = (i % 2) ? '<' : '>';
        wattron(arenaWin, COLOR_PAIR(i + 1));
        mvwprintw(arenaWin, players[i].y, players[i].x, "%c", 236);
        if (numPlayers == 3){
            players[2].direction = '^';
            mvwprintw(arenaWin, players[i].y, players[i].x, "8");
        }
        wattroff(arenaWin, COLOR_PAIR(i + 1));
        players[i].oldDirection = 'o';
        gameArena[players[i].y][players[i].x] = 'o';
    }

    for (int i = 0; i < 4; i++) free(names[i]);
    free(names);
}

int playerInput(Player* players){
    int* pressedKeys = (int*)malloc(sizeof(int) * 50), count = 0;
    int in;
    while ((in = wgetch(stdscr)) != ERR){
        pressedKeys[count] = in;
        count++;
        if (count > 50) pressedKeys = (int*)realloc(pressedKeys, sizeof(int) * (50 + count));
    }
    
    for (int i = 0; i <= twoHuman; i++) players[i].oldDirection = players[i].direction;
    for (int i = 0; i < count; i++){
        switch(pressedKeys[i]){
            case 'w':
                if (players[0].oldDirection != 'v') players[0].direction = '^';
                break;
            case 's':
                if (players[0].oldDirection != '^') players[0].direction = 'v';
                break;
            case 'a':
                if (players[0].oldDirection != '>') players[0].direction = '<';
                break;
            case 'd':
                if (players[0].oldDirection != '<') players[0].direction = '>';
                break;
            case KEY_UP:
                if (players[twoHuman].oldDirection != 'v') players[twoHuman].direction = '^';
                break;
            case KEY_DOWN:
                if (players[twoHuman].oldDirection != '^') players[twoHuman].direction = 'v';
                break;
            case KEY_LEFT:
                if (players[twoHuman].oldDirection != '>') players[twoHuman].direction = '<';
                break;
            case KEY_RIGHT:
                if (players[twoHuman].oldDirection != '<') players[twoHuman].direction = '>';
                break;
            case (char)8:
                free(pressedKeys);
                return true;
            case (char)27:
                free(pressedKeys);
                quit = 1;
                return true;
        }
    }
    return false;
}

void computerInput(char** gameArena, Player* players, int i){
    if (!players[i].alive) return;
    bool turn = false;
    players[i].oldDirection = players[i].direction;
    switch (players[i].direction){
        case '^':
            turn = (gameArena[players[i].y - 1][players[i].x] == 'x' || gameArena[players[i].y - 1][players[i].x] == 'o');
            players[i].direction = (!turn) ? '^' : (rand() % 2) ? '<' : '>';
            break;
        case 'v':
            turn = (gameArena[players[i].y + 1][players[i].x] == 'x' || gameArena[players[i].y + 1][players[i].x] == 'o');
            players[i].direction = (!turn) ? 'v' : (rand() % 2) ? '<' : '>';
            break;
        case '<':
            turn = (gameArena[players[i].y][players[i].x - 1] == 'x' || gameArena[players[i].y][players[i].x - 1] == 'o');
            players[i].direction = (!turn) ? '<' : (rand() % 2) ? '^' : 'v';
            break;
        case '>':
            turn = (gameArena[players[i].y][players[i].x + 1] == 'x' || gameArena[players[i].y][players[i].x + 1] == 'o');
            players[i].direction = (!turn) ? '>' : (rand() % 2) ? '^' : 'v';
            break;
    }

    
}

void updateMoves(char** gameArena, Player* players){
    for (int i = 0; i < numPlayers; i++){
        if (!players[i].alive) continue;

        gameArena[players[i].y][players[i].x] = 'x';
        switch(players[i].direction){
            case '^':
                players[i].y--;
                break;
            case 'v':
                players[i].y++;
                break;
            case '>':
                players[i].x++;
                break;
            case '<':
                players[i].x--;
                break;
        }
        if (gameArena[players[i].y][players[i].x] == ' ') gameArena[players[i].y][players[i].x] = 'o';
    }
}

void checkCollisions(char** gameArena, Player* players){
    for (int i = 0; i < numPlayers; i++){
        if (!players[i].alive) continue;
        players[i].alive = !(gameArena[players[i].y][players[i].x] == 'x');
    }

    for (int i = 0; i < numPlayers; i++){
        if (players[i].alive) continue;
        killColor(gameArena, i);
    }

}

void killColor(char** gameArena, int color){
    for (int y = 1; y < 25; y++){
        for (int x = 1; x < 120; x++){
            chtype ch = mvwinch(arenaWin, y, x);
            if ((ch & A_COLOR) == COLOR_PAIR(color + 1)){
                gameArena[y][x] = ' ';
                mvwprintw(arenaWin, y, x, " ");
            }
        }
    }
}

void updateScreen(Player* players){
    for (int i = 0; i < numPlayers; i++){
        if (!players[i].alive) continue;

        wattron(arenaWin, COLOR_PAIR(i + 1));
        switch(players[i].direction){
            case '^':
                mvwprintw(arenaWin, players[i].y + 1, players[i].x, "|");
                mvwprintw(arenaWin, players[i].y, players[i].x, "8");
                break;
            case 'v':
                mvwprintw(arenaWin, players[i].y - 1, players[i].x, "|");
                mvwprintw(arenaWin, players[i].y, players[i].x, "8");
                break;
            case '>':
                mvwprintw(arenaWin, players[i].y, players[i].x - 1, "-");
                mvwprintw(arenaWin, players[i].y, players[i].x, "%c", 236);
                break;
            case '<':
                mvwprintw(arenaWin, players[i].y, players[i].x + 1, "-");
                mvwprintw(arenaWin, players[i].y, players[i].x, "%c", 236);
                break;
        }
        wattroff(arenaWin, COLOR_PAIR(i + 1));
    }
    wrefresh(arenaWin);

    for (int i = 0; i < numPlayers; i++){
        wattron(statusWin, COLOR_PAIR(i + 1));
        mvwprintw(statusWin, 1, 1 + (30 * i), "%s", players[i].name);
        wattroff(statusWin, COLOR_PAIR(i + 1));
        mvwprintw(statusWin, 2, 1 + (30 * i), "%s", (players[i].alive) ? "Alive" : "Dead  ");
        mvwprintw(statusWin, 3, 1 + (30 * i), "%c", (players[i].alive) ? players[i].direction : 'O');
    }
    wrefresh(statusWin);
}

int checkWinner(Player* players){
    int count = 0;
    for (int i = 0; i < numPlayers; i++) if (players[i].alive) count++;
    if (count == 0) return 0;
    else if (count == 1) for (int i = 0; i < 4; i++) if (players[i].alive) return (i + 1);
    return -1;
}

void endGame(Player* players, int win){
    wclear(statusWin);
    box(statusWin, 0, 0);

    char message[50];
    if (win == 0) sprintf(message, "All players died. Tie!");
    else sprintf(message, "%s won!", players[win - 1].name);
    mvwprintw(statusWin, 1, 58 - strlen(message) / 2, message);

    strcpy(message, "Press escape to close or space to continue to menu.");
    mvwprintw(statusWin, 3, 58 - strlen(message) / 2, message);
    
    wrefresh(statusWin);

    char c;
    do c = (char)getch(); 
    while(c != 27 && c != 32);
    if (c == 27) quit = 1;
}

void clearMem(char** gameArena, Player* players){
    for (int i = 0; i < 25; i++) free(gameArena[i]);
    free(gameArena);
    free(players);

    wclear(arenaWin);
    wclear(statusWin);
    clear();

    wrefresh(arenaWin);
    wrefresh(statusWin);
    refresh();

    free(arenaWin);
    free(statusWin);
}