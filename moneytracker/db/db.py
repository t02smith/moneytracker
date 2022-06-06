from moneytracker.db.create import *
import datetime
from dateutil.parser import isoparse

# CREATE TABLE

create_accounts()
create_expenses()
create_budgets()
load_default_budget_data()
create_recurring_payments()


# DATABASE INTERACTIONS


def insert_expense(expense: Expense):
    expense_id = hash(expense)
    with conn:
        c.execute("INSERT INTO expenses VALUES (:id, :reason, :cat, :date, :amount, :acc)",
                  {"id": expense_id, "reason": expense.reason, "cat": expense.category.name,
                   "amount": expense.amount, "date": expense.date.isoformat(), "acc": expense.account.id})
    return expense_id


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
    """
    Collects expenses by a specific category
    :param n: max number of records to fetch
    :param start_date: oldest date of a record
    :return: list of expense objects
    """
    if start_date is None:
        start_date = datetime.datetime(1, 1, 1)

    with conn:
        c.execute("""
            SELECT expenses.*, accounts.*
            FROM expenses
            INNER JOIN accounts ON expenses.account_id = accounts.id
            WHERE datetime > :dt
            ORDER BY datetime DESC
            LIMIT :n
        """, {"n": n, "dt": start_date.isoformat()})

    res = c.fetchall()
    return parse_expenses(res)


def get_expenses_by_category(n: int, ecat: ExpenseCategory, start_date: datetime = None):
    """
    Collects expenses by a specific category
    :param n: max number of records to fetch
    :param ecat: the category of records to select
    :param start_date: oldest date of a record
    :return: list of expense objects
    """
    if start_date is None:
        start_date = datetime.datetime(1, 1, 1)

    with conn:
        c.execute("""
            SELECT expenses.*, accounts.*
            FROM expenses
            INNER JOIN accounts ON expenses.account_id = accounts.id
            WHERE category=:ecat AND datetime > :dt
            LIMIT :n
        """, {"n": n, "ecat": ecat.name, "dt": start_date.isoformat()})

    res = c.fetchall()
    return parse_expenses(res)


def parse_expenses(expense_account_records):
    """
    Takes the output of the joined expense-account table to objs
    :param expense_account_records: List of expense-account records
    :return: list of expense objects
    """
    expenses = []
    for r in expense_account_records:
        acc = Account(*(r[-3:]))
        expenses.append(Expense(
            id=r[0], reason=r[1], category=ExpenseCategory[r[2]], date=isoparse(r[3]),
            amount=r[4], account=acc
        ))

    return expenses


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
            INSERT INTO accounts (id, account_name, balance)
            VALUES (:id, :name, :balance)
        """, {"id": account_id, "name": name, "balance": balance})


def change_balance(account: Account, add_to: float):
    new_balance = account.balance + add_to
    with conn:
        c.execute("""
            UPDATE accounts
            SET balance = :balance
            WHERE id = :acc_id
        """, {"balance": new_balance, "acc_id": account.id})
    return new_balance


# Recurring Payments

def setup_recurring_payment(expense: Expense, time_frame: TimeFrame):
    """
    Adds a new recurring payment
    :param expense: the payment
    :param time_frame: how often to make the payment
    :return: void
    """
    expense_id = hash((expense, time_frame, datetime.datetime.now()))
    with conn:
        c.execute("""
            INSERT INTO recurring_payments (id, expense_id, time_frame, last_paid)
            VALUES (:id, :eid, :tf, :last_paid)
        """, {"id": expense_id, "eid": expense.id, "tf": time_frame.name,
              "last_paid": datetime.datetime.now().isoformat()})


def get_recurring_payments():
    """
    Gets a list of all recurring payments
    :return: recurring payment list
    """
    with conn:
        c.execute("""
            SELECT expenses.*, accounts.*, recurring_payments.id, recurring_payments.time_frame,
                   recurring_payments.last_paid
            FROM recurring_payments
            INNER JOIN expenses on expenses.id = recurring_payments.expense_id
            INNER JOIN accounts on accounts.id = expenses.account_id
        """)
    res = c.fetchall()
    recurring_payments = []

    for r in res:
        acc = Account(id=r[6], account_name=r[7], balance=r[8])
        exp = Expense(
            id=r[0], reason=r[1], category=ExpenseCategory[r[2]], date=isoparse(r[3]),
            amount=r[4], account=acc
        )
        recurring_payments.append(RecurringExpense(r[-3], exp, TimeFrame[r[-2]], isoparse(r[-1])))

    return recurring_payments
