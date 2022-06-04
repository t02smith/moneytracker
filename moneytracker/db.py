import sqlite3
from moneytracker.model import *
import datetime

conn = sqlite3.connect("./finances.db")
c = conn.cursor()


# CREATE TABLE

def create_expenses():
    # expenses table with expenses
    with conn:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY NOT NULL,
                reason TEXT,
                category TEXT,
                datetime TEXT NOT NULL,
                amount REAL NOT NULL,
                account_id INTEGER NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
        """)


def create_budgets():
    # Given budgets for a given time period
    with conn:
        c.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY NOT NULL,
                budget REAL NOT NULL,
                time_frame TEXT NOT NULL
            )
        """)


def load_default_budget_data():
    # Set all default budgets to £0
    with conn:
        for cat in list(ExpenseCategory):
            c.execute("""
                INSERT OR IGNORE INTO budgets (category, budget, time_frame)
                VALUES (:cat, :default_budget, :tf)
            """, {"cat": cat.name, "default_budget": 0, "tf": TimeFrame.MONTH.name})


def create_accounts():
    with conn:
        c.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY NOT NULL,
                account_name TEXT NOT NULL UNIQUE,
                balance REAL NOT NULL
            )
        """)


create_accounts()
create_expenses()
create_budgets()
load_default_budget_data()


# DATABASE INTERACTIONS


def insert_expense(expense: Expense):
    expense_id = hash(expense)
    with conn:
        c.execute("INSERT INTO expenses VALUES (:id, :reason, :cat, :date, :amount, :acc)",
                  {"id": expense_id, "reason": expense.reason, "cat": expense.category.name,
                   "amount": expense.amount, "date": expense.date.isoformat(), "acc": expense.account})


def get_by_category(ecat: ExpenseCategory, tf: TimeFrame = None):
    if tf is None:
        tf = TimeFrame.FOREVER

    oldest_t = oldest_time(tf)

    with conn:
        c.execute("""
            SELECT budgets.category, SUM(expenses.amount) AS amount, budget 
            FROM budgets 
            INNER JOIN expenses 
            ON expenses.category = budgets.category
            WHERE expenses.datetime > :oldest AND expenses.category=:ecat
            GROUP BY budgets.category
        """, {"oldest": oldest_t.isoformat(), "ecat": ecat.name})

    res = c.fetchone()
    return None if res is None else ExpenseCategoryOverview(*res)


def set_budget(ecat: ExpenseCategory, amount: float, tf: TimeFrame):
    old = get_budget_by_category(ecat)
    if old is not None:
        if old[0] == amount:
            return old[1]

    with conn:
        c.execute("""
            INSERT INTO budgets (category, budget, time_frame)
            VALUES (:cat, :amount, :tf)
            ON CONFLICT (category)
            DO UPDATE SET budget=:amount
        """, {"cat": ecat.name, "amount": amount, "tf": tf.name})

    return None if old is None else old[1]


def get_budget():
    with conn:
        c.execute("""
            SELECT * 
            FROM budgets
        """)

    res = c.fetchall()
    return [Budget(*x) for x in res]


def get_budget_by_category(ecat: ExpenseCategory):
    with conn:
        c.execute("SELECT * FROM budgets WHERE category=:cat", {"cat": ecat.name})
    return c.fetchone()


def get_expenses(n: int, start_date: datetime = None):
    if start_date is None:
        start_date = datetime.datetime(1, 1, 1)

    with conn:
        c.execute("""
            SELECT amount, category, reason, datetime, account_id
            FROM expenses
            WHERE datetime > :dt
            ORDER BY datetime DESC
            LIMIT :n
        """, {"n": n, "dt": start_date.isoformat()})

    res = c.fetchall()
    return [Expense(*x) for x in res]


def get_expenses_by_category(n: int, ecat: ExpenseCategory, start_date: datetime = None):
    if start_date is None:
        start_date = datetime.datetime(1, 1, 1)

    with conn:
        c.execute("""
            SELECT amount, category, reason, datetime, account_id
            FROM expenses
            WHERE category=:ecat AND datetime > :dt
            LIMIT :n
        """, {"n": n, "ecat": ecat.name, "dt": start_date.isoformat()})

    res = c.fetchall()
    return [Expense(*x) for x in res]


def get_timeframe(ecat: ExpenseCategory):
    with conn:
        c.execute("""
            SELECT time_frame
            FROM budgets
            WHERE category=:ecat
        """, {"ecat": ecat.name})

    res = c.fetchone()
    if res is None:
        return TimeFrame.MONTH

    return TimeFrame[res[0]]


# CLEAR


def clear_all():
    """
    Clears all data within all tables
    :return: void
    """
    with conn:
        c.execute("DROP TABLE IF EXISTS expenses")


def clear_by_category(ecat: ExpenseCategory):
    """
    Clears all data with a given category
    :param ecat: the category to remove
    :return: void
    """
    with conn:
        c.execute("""
            DELETE FROM expenses
            WHERE category = :ecat
        """, {"ecat": ecat.name})
        c.execute("""
            DELETE FROM budgets
            WHERE category = :ecat
        """, {"ecat": ecat.name})


# ACCOUNTS


def get_accounts():
    with conn:
        c.execute("SELECT * FROM accounts")

    res = c.fetchall()
    return [Account(*x) for x in res]


def get_account_by_id(acc_id: int):
    with conn:
        c.execute("SELECT * FROM accounts WHERE id=:acc_id", {"acc_id": acc_id})

    res = c.fetchone()
    return None if res is None else Account(*res)


def get_account_by_name(name: str):
    with conn:
        c.execute("""
            SELECT *
            FROM accounts
            WHERE account_name=:name
        """, {"name": name})

    res = c.fetchone()
    return None if res is None else Account(*res)


def add_account(name: str, balance: float):
    account_id = hash((name, balance, datetime.datetime.now()))
    with conn:
        c.execute("""
            INSERT OR IGNORE INTO accounts (id, account_name, balance)
            VALUES (:id, :name, :balance)
        """, {"id": account_id, "name": name, "balance": balance})


def change_balance(account_id: int, add_to: float):
    acc = get_account_by_id(account_id)
    new_balance = acc.balance + add_to
    with conn:
        c.execute("""
            UPDATE accounts
            SET balance = :balance
            WHERE id = :acc_id
        """, {"balance": new_balance, "acc_id": account_id})
