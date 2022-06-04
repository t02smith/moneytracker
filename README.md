# Moneytracker

Moneytracker is a command line tool to help you track your finances,
written in Python using SQLite3, Typer & Rich.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

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
python main.py [COMMAND_NAME] [ARG1] [ARG2] ....
```

You can find more information about commands, such as arguments, by running:
```bash
python main.py [COMMAND_NAME] --help
```

- **overview** - Gives a rundown of your expenses by category including 
total amount spent and budget remaining
- **spend** - Add an expense
- **deposit** - Add some income
- **budget** - Set the budget for a category
- **categories** - Gives a rundown about all the expense categories 
including descriptions, budget & time frame
- **expenses** - Gives a rundown of the last N expenses. Can be filtered
by category
- **clear** - Clear all expenses and budget config
- **account** - Create a new account
- **accounts** - Outputs an overview of accounts

## Database Tables

### expenses

Stores all expenses made.

```sqlite
CREATE TABLE expenses (
                id INTEGER PRIMARY KEY NOT NULL,
                reason TEXT,
                category TEXT,
                datetime TEXT NOT NULL,
                amount REAL NOT NULL,
                account_id INTEGER NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
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

### accounts

Stores account information.

```sqlite
CREATE TABLE accounts (
                id INTEGER PRIMARY KEY NOT NULL,
                account_name TEXT NOT NULL UNIQUE,
                balance REAL NOT NULL
            );
```

## Todo

- <span style="color:green">~~Support for many accounts~~</span>
- Recurring payments
- Extra/custom categories
- Time frame with specific dates
- Account total in/out in accounts command
