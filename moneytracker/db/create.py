import sqlite3
from moneytracker.model import *

conn = sqlite3.connect("./finances.db")
c = conn.cursor()

# Expenses


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


# Budget


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


# Account

def create_accounts():
    with conn:
        c.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY NOT NULL,
                account_name TEXT NOT NULL UNIQUE,
                balance REAL NOT NULL
            )
        """)
        
        
# Recurring Payments


def create_recurring_payments():
    with conn:
        c.execute("""
            CREATE TABLE IF NOT EXISTS recurring_payments (
                id INTEGER PRIMARY KEY NOT NULL,
                expense_id INTEGER NOT NULL,
                time_frame TEXT NOT NULL,
                last_paid TEXT NOT NULL,
                FOREIGN KEY (expense_id) REFERENCES expenses(id)
            )        
        """)
