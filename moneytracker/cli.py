import typer
from typing import Optional, List

from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from rich.progress_bar import ProgressBar

from moneytracker.db.db import *

from dateutil.parser import isoparse
from datetime import datetime

console = Console()
app = typer.Typer()


@app.command(short_help="Document an expense")
def spend(amount: float = typer.Option(..., "--amount", "-m", help="How much was spent"),
          account_name: str = typer.Option(..., "--account", "-a", help="Which account it was taken from"),
          category: Optional[str] = typer.Option("GENERAL", "--category", "-c", help="Context information"),
          reason: Optional[str] = typer.Option("", "--reason", "-r", help="Why the expense was made")):
    """
    Submit a record about money spent in a given payment\n
    :param account_name: Name of the account used
    :param amount: How much was spent
    :param category: The category the payment fell into
    :param reason: The reason for the payment
    :return: void
    """
    acc = get_account_by_name(account_name)
    insert_expense(
        Expense(-1, reason, ExpenseCategory[category], datetime.now(), amount, acc))
    new_balance = change_balance(acc, -1*amount)

    console.print("Adding expense {amount:.2f} for {reason} to {name}"
                  .format(amount=amount, reason=category, name=account_name))
    console.print("Account [bold green]{name}[/bold green]'s balance changed [bold red]{old:.2f}[/bold red] -> "
                  "[bold blue]{new:.2f}[/bold blue]"
                  .format(name=acc.account_name, old=acc.balance, new=new_balance))


@app.command(short_help="Document a deposit")
def deposit(amount: float = typer.Option(..., "--amount", "-m", help="How much was received"),
            account_name: str = typer.Option(..., "--account", "-a", help="Which account it was added to"),
            category: Optional[str] = typer.Option("GENERAL", "--category", "-c", help="Context information"),
            reason: Optional[str] = typer.Option("", "--reason", "-r", help="Why the deposit was made")):
    """
    Submit a record about some money entering your account(s)
    :param account_name: Name of account used
    :param amount: How much was added
    :param category: The category the deposit falls into
    :param reason: The reason for the deposit
    :return: void
    """
    acc = get_account_by_name(account_name)
    insert_expense(
        Expense(-1*amount, ExpenseCategory[category], reason, datetime.now(), acc))
    new_balance = change_balance(acc, amount)

    console.print("Adding deposit {amount:.2f} for {reason} to {name}"
                  .format(amount=amount, reason=category, name=account_name))
    console.print("Account [bold green]{name}[/bold green]'s balance changed [bold red]{old:.2f}[/bold red] -> "
                  "[bold blue]{new:.2f}[/bold blue]"
                  .format(name=acc.account_name, old=acc.balance, new=new_balance))


@app.command(short_help="Gives an overview by category")
def overview():
    """
    Gives an overview of categories and their expenses
    :return: void
    """
    table = Table(show_header=True, header_style="bold magenta", show_edge=False,
                  title="Overview", title_style="bold green")
    table.add_column("Category", width=8)
    table.add_column("Net", width=10)
    table.add_column("Budget", width=25)
    table.add_column("Remaining", width=10)

    def remaining_amount_colour(total: int, leftover: int):
        if total == 0:
            return "red1"

        ratio = leftover/total
        if ratio >= 1:
            return "red1"
        elif ratio >= 0.7:
            return "orange_red1"
        elif ratio >= 0.4:
            return "yellow"
        else:
            return "green"

    for ecat in list(ExpenseCategory):
        tf = get_timeframe(ecat)
        res = get_by_category(ecat, tf)

        if res is None:
            continue

        colour = get_colour_from_category(ecat)
        progress = ProgressBar(
            total=res.budget if res.budget > 0 else 1,
            completed=0 if res.amount_spent >= res.budget else res.budget - res.amount_spent,
            width=25
        )
        table.add_row(f"[{colour}]{ecat.name}[/{colour}]", "[bold]£{amount:.2f}[/bold]"
                      .format(amount=res.amount_spent), progress,
                      "[bold {colour}]£{amount:.2f}[/bold {colour}]"
                      .format(amount=res.budget - res.amount_spent,
                              colour=remaining_amount_colour(res.budget, res.amount_spent)))

    console.print(table)


@app.command(short_help="Set a budget")
def budget(category: str = typer.Option(..., "--category", "-c", help="Which category you're updating"),
           amount: float = typer.Option(..., "--amount", "-m", help="The new budget for this category"),
           timeframe: Optional[str] =
           typer.Option("MONTH", "--time-frame", "-t",
                        help="The length of time an expense is considered part of the budget")):
    """
    Set the budget of a given category\n
    :param timeframe: Time period for which a budget lasts
    :param category: the category to update
    :param amount: the new budget
    :return: void
    """
    ecat = ExpenseCategory[category]
    tf = TimeFrame[timeframe]
    old = set_budget(ecat, amount, tf)
    if old is None:
        console.print("[bold green]Set {category} budget to {amount:.2f}[/bold green]"
                      .format(category=category, amount=amount))
    else:
        if old == amount:
            console.print("Category [bold {colour}]{category}[/bold {colour}] is already [bold red1]"
                          "{amount:.2f}[/bold red1]"
                          .format(category=category, colour=get_colour_from_category(ecat), amount=amount))
        else:
            console.print("Updating [bold {colour}]{category}[/bold {colour}] budget from [bold orange]"
                          "{old:.2f}[/bold orange] to [bold green]{new:.2f}[/bold green]"
                          .format(category=category, old=old, new=amount, colour=get_colour_from_category(ecat)))


@app.command(short_help="Show a list of categories and their budget")
def categories():
    """
    Gives a rundown of all categories, their budget and purpose
    :return: void
    """
    budgets = get_budget()
    table = Table(show_header=True, header_style="bold blue", show_edge=False,
                  title="Your Budget", title_style="bold green1")
    table.add_column("Category", width=10)
    table.add_column("Description", width=40)
    table.add_column("Budget", width=10, justify="right")
    table.add_column("Time Frame", width=10, justify="right")

    for row in budgets:
        ecat = ExpenseCategory[row.category]
        ecat_colour = get_colour_from_category(ecat)
        table.add_row(f"[bold {ecat_colour}]{row.category}[/bold {ecat_colour}]",
                      f"[italic]{ecat.description()}[/italic]",
                      "[bold]£{amount:.2f}[/bold]".format(amount=row.amount), row.time_frame)

    console.print(table)


@app.command(short_help="List of expenses")
def expenses(
        category: Optional[List[str]] = typer.Option([], "--category", "-c",  help="Filter by category"),
        n: Optional[int] = typer.Option(10, "--record-count", "-n", help="The number of results wanted"),
        start_date: Optional[str] = typer.Option(None, "--start-date", "-t",
                                                 help="List relevant transactions from this date")):
    """
    Generates a table of expenses\n
    :param start_date: Will only fetch transactions from this date (in isoformat)
    :param category: (optional) filter by category
    :param n: (optional) only show last n expenses [default = 10]
    :return: void
    """
    if len(category) == 0:
        res = get_expenses(n, None if start_date is None else isoparse(start_date))
    else:
        res_ls = [get_expenses_by_category(n, ExpenseCategory[ecat]) for ecat in category]
        res = []
        for each_cat in res_ls:
            res += each_cat

    table = Table(show_header=True, header_style="bold blue", show_edge=False,
                  title="Your Expenses", title_style="bold green1")
    table.add_column("Category", width=10)
    table.add_column("Amount", width=8, justify="right")
    table.add_column("Account", width=12)
    table.add_column("Date", width=10, justify="right")
    table.add_column("Time", width=6, justify="right")
    table.add_column("Reason", width=30)

    for row in res:
        tf = get_timeframe(row.category)

        if not is_within_time_frame(tf, row.date):
            continue

        ecat_colour = get_colour_from_category(row.category)
        table.add_row(f"[bold {ecat_colour}]{row.category.name}[/bold {ecat_colour}]",
                      "[bold]£{amount:.2f}[/bold]".format(amount=row.amount), row.account.account_name,
                      f"{row.date.day}/{row.date.month}/{row.date.year}",
                      "{hour}:{mins}".format(hour=str(row.date.hour).rjust(2, '0'), mins=str(row.date.minute).rjust(2, '0')),
                      f"[dim italic]{row.reason}[/dim italic]")

    console.print(table)


@app.command(short_help="Clears/resets all expense and budget data.")
def clear(category: Optional[str] = typer.Option(None, "--category", "-c")):
    """
    Clear data from the databases\n
    :param category: (optional) remove records of a certain category
    :return: void
    """
    console.print("[bold red]Clearing will remove all of your expense data.[/bold red]")
    ask = Confirm.ask("Are you sure you want to clear? ")

    if ask == "N":
        console.print("[italic]Clear cancelled[/italic]")
        return

    if category is None:
        console.print("[italic]Clearing all data[/italic]")
        clear_all()
    else:
        console.print(f"[italic]Clearing {category} data[/italic]")
        clear_by_category(ExpenseCategory[category])

    create_expenses()
    create_budgets()
    load_default_budget_data()
    console.print("[green]Data cleared[/green]")


# ACCOUNTS

@app.command(short_help="Add a new account")
def account(name: str, balance: Optional[float] = typer.Option(0, "--balance", "-b")):
    """
    Create a new account. Accounts must have unique names\n
    :param name: Name of the account
    :param balance: Initial account balance
    :return: void
    """
    try:
        add_account(name, balance)
        console.print("[green]Account {name} created successfully with balance {amount:.2f}[/green]"
                      .format(name=name, amount=balance))
    except sqlite3.IntegrityError as e:
        console.print(f"[red]Error creating account {name}[/red]")
        console.print(f"[italic dim]{e}[/italic dim]")


@app.command(short_help="List accounts")
def accounts():
    """
    Outputs a list of accounts
    :return: void
    """
    account_list = get_accounts()
    table = Table(show_header=True, header_style="bold blue", show_edge=False,
                  title="Your Accounts", title_style="bold green1")
    table.add_column("Account Name", width=12)
    table.add_column("Balance", width=10, justify="right")

    for acc in account_list:
        table.add_row(f"[bold]{acc.account_name}[/bold]",
                      "£{balance:.2f}".format(balance=acc.balance))

    console.print(table)


@app.command(short_help="Add a recurring payment")
def recur(
        amount: float,
        account_name: str,
        category: Optional[str] = typer.Option("GENERAL", "--category", "-c", help="Context information"),
        reason: Optional[str] = typer.Option("", "--reason", "-r", help="Why the expense was made"),
        time_frame: Optional[str] = typer.Option("MONTH", "--time-frame", "-t", help="Payment occurs ever...")
):
    acc = get_account_by_name(account_name)
    expense = Expense(-1, reason, ExpenseCategory[category], datetime.now(), amount, acc)
    expense.id = insert_expense(expense)
    change_balance(acc, -1 * amount)
    setup_recurring_payment(expense, TimeFrame[time_frame])
    console.print("[bold green]Setup recurring payment to {acc} for {amount:.2f} every {tf}[/bold green]"
                  .format(acc=acc.account_name, amount=amount, tf=time_frame))


@app.command(short_help="Outputs recurring payments")
def recurring():
    recurring_ls = get_recurring_payments()
    table = Table(show_header=True, header_style="bold blue", show_edge=False,
                  title="Your Payments", title_style="bold green1")
    table.add_column("Category", width=10)
    table.add_column("Amount", width=8, justify="right")
    table.add_column("Account", width=10)
    table.add_column("Last Paid", width=15, justify="right")
    table.add_column("Pay Every", width=10, justify="right")
    table.add_column("Reason", width=30)

    for re in recurring_ls:
        ecat_colour = get_colour_from_category(re.expense.category)
        table.add_row(
            f"[bold {ecat_colour}]{re.expense.category.name}[/bold {ecat_colour}]",
            "£{amount:.2f}".format(amount=re.expense.amount),
            re.expense.account.account_name,
            f"{re.last_paid.day}/{re.last_paid.month}/{re.last_paid.year} {re.last_paid.hour}:{re.last_paid.minute}",
            re.recur_every.name, re.expense.reason
        )

    console.print(table)
