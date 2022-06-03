import sqlite3
from moneytracker.model import Expense, ExpenseCategory
import datetime

conn = sqlite3.connect("./finances.db")
c = conn.cursor()


# CREATE TABLE

# expenses table with expenses
c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY NOT NULL,
        reason TEXT,
        category TEXT,
        datetime TEXT NOT NULL,
        amount REAL NOT NULL
    )
""")


# Given budgets for a given time period
c.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        category TEXT PRIMARY KEY NOT NULL,
        budget REAL NOT NULL
    )
""")


# Set all default budgets to £0
with conn:
    for cat in list(ExpenseCategory):
        c.execute("""
            INSERT OR IGNORE INTO budgets (category, budget)
            VALUES (:cat, :default_budget)
        """, {"cat": cat.name, "default_budget": 0})


# DATABASE INTERACTIONS

def insert_expense(expense: Expense):
    expense_id = hash(expense)
    with conn:
        c.execute("INSERT INTO expenses VALUES (:id, :reason, :cat, :date, :amount)",
                  {"id": expense_id, "reason": expense.reason, "cat": expense.category.name,
                   "amount": expense.amount, "date": expense.date.isoformat()})


def get_by_categories():
    with conn:
        c.execute("""
            SELECT budgets.category, SUM(expenses.amount) AS amount, budget 
            FROM budgets 
            INNER JOIN expenses 
            ON expenses.category = budgets.category
            GROUP BY budgets.category
        """)

    return c.fetchall()


def set_budget(ecat: ExpenseCategory, amount: float):
    old = get_budget_by_category(ecat)
    if old is not None:
        if old[0] == amount:
            return old[1]

    with conn:
        c.execute("""
            INSERT INTO budgets (category, budget)
            VALUES (:cat, :amount)
            ON CONFLICT (category)
            DO UPDATE SET budget=:amount
        """, {"cat": ecat.name, "amount": amount})

    return None if old is None else old[1]


def get_budget():
    with conn:
        c.execute("SELECT * FROM budgets")
    return c.fetchall()


def get_budget_by_category(ecat: ExpenseCategory):
    with conn:
        c.execute("SELECT * FROM budgets WHERE category=:cat", {"cat": ecat.name})
    return c.fetchone()


def get_expenses(n: int):
    with conn:
        c.execute("""
            SELECT *
            FROM expenses
            ORDER BY datetime DESC
            LIMIT :n
        """, {"n": n})

    return c.fetchall()


def get_expenses_by_category(n: int, ecat: ExpenseCategory):
    with conn:
        c.execute("""
            SELECT *
            FROM expenses
            WHERE category=:ecat
            LIMIT :n
        """, {"n": n, "ecat": ecat.name})

    return c.fetchall()
