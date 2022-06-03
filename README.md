# Moneytracker

Moneytracker is a command line tool to help you track your finances,
written in Python using SQLite3, Typer & Rich.

## Categories

Expenses should be split into categories to give contextual information
about an expense without the need for a reason. 

- **UTILITY** - Money spent on bills (e.g. rent, water, gas, ...)
- **FOOD** - Money spent on food including going out to eat
- **HAZARD** - Unexpected payments for repairs or emergency costs
- **TREAT** - Unnecessary purchases as a treat to yourself
- **WAGE** - Income from employment or expense for employees
- **GIFT** - Gifts for other people (e.g. birthdays)
- **GENERAL** - (default) For everything else 

## Commands

Commands can currently be called using:

```bash
python main.py [COMMAND_NAME] [ARG1] [ARGS2] ....
```

- **overview** - *Gives a rundown of your expenses by category including 
total amount spent and budget remaining*
- **spend [amount] [category] [reason]** - Add an expense
- **deposit [amount] [category] [reason]** - Add some income
- **budget [category] [amount]** - Set the budget for a category

## Database Tables

### expenses

Stores all expenses made.

```sqlite
CREATE TABLE expenses (
        id INTEGER PRIMARY KEY NOT NULL,
        reason TEXT,
        category TEXT,
        datetime TEXT NOT NULL,
        amount REAL NOT NULL
    );
```


### budgets

Stores the budget categories' configuration.

```sqlite
CREATE TABLE budgets (
        category TEXT PRIMARY KEY NOT NULL,
        budget REAL NOT NULL,
        time_frame TEXT NOT NULL
    );
```