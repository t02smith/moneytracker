import typer
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.progress_bar import ProgressBar

from moneytracker.model import *
from moneytracker.db import *

from dateutil.parser import isoparse

console = Console()
app = typer.Typer()


@app.command(short_help="Document an expense")
def spend(amount: float, category: Optional[str] = typer.Option("GENERAL"), reason: Optional[str] = typer.Option("")):
    """
    Submit a record about money spent in a given payment\n
    :param amount: How much was spent
    :param category: The category the payment fell into
    :param reason: The reason for the payment
    :return: void
    """
    insert_expense(Expense(amount, ExpenseCategory[category], reason, datetime.datetime.now()))


@app.command(short_help="Document a deposit")
def deposit(amount: float, category: Optional[str] = typer.Option("GENERAL"), reason: Optional[str] = typer.Option("")):
    """
    Submit a record about some money entering your account(s)
    :param amount: How much was added
    :param category: The category the deposit falls into
    :param reason: The reason for the deposit
    :return: void
    """
    insert_expense(Expense(-1 * amount, ExpenseCategory[category], reason))


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

        print(res)

        colour = get_colour_from_category(ecat)
        progress = ProgressBar(
            total=res[2] if res[2] > 0 else 1,
            completed=0 if res[1] >= res[2] else res[2] - res[1],
            width=25
        )
        table.add_row(f"[{colour}]{ecat.name}[/{colour}]", "[bold]£{amount:.2f}[/bold]"
                      .format(amount=res[1]), progress,
                      "[bold {colour}]£{amount:.2f}[/bold {colour}]"
                      .format(amount=res[2] - res[1], colour=remaining_amount_colour(res[2], res[1])))

    console.print(table)


@app.command(short_help="Set a budget")
def budget(category: str, amount: float, timeframe: Optional[str] = typer.Option("MONTH")):
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
        ecat = ExpenseCategory[row[0]]
        ecat_colour = get_colour_from_category(ecat)
        table.add_row(f"[bold {ecat_colour}]{row[0]}[/bold {ecat_colour}]", f"[italic]{ecat.description()}[/italic]",
                      "[bold]£{amount:.2f}[/bold]".format(amount=row[1]), row[2])

    console.print(table)


@app.command(short_help="List of expenses")
def expenses(
        category: Optional[str] = typer.Option(None, help="Filter by category"),
        n: Optional[int] = typer.Option(10, help="The number of results wanted")):
    """
    Generates a table of expenses\n
    :param category: (optional) filter by category
    :param n: (optional) only show last n expenses [default = 10]
    :return: void
    """
    res = get_expenses(n, datetime.datetime(2020,10,5)) if category is None \
        else get_expenses_by_category(n, ExpenseCategory[category])
    table = Table(show_header=True, header_style="bold blue", show_edge=False,
                  title="Your Expenses", title_style="bold green1")
    table.add_column("Category", width=10)
    table.add_column("Amount", width=8, justify="right")
    table.add_column("Date", width=10, justify="right")
    table.add_column("Time", width=6, justify="right")
    table.add_column("Reason", width=30)

    for row in res:
        ecat = ExpenseCategory[row[2]]
        tf = get_timeframe(ecat)
        dt = isoparse(row[3])

        if not is_within_time_frame(tf, dt):
            continue

        ecat_colour = get_colour_from_category(ecat)
        table.add_row(f"[bold {ecat_colour}]{row[2]}[/bold {ecat_colour}]", f"[bold]{row[4]}[/bold]",
                      f"{dt.day}/{dt.month}/{dt.year}",
                      "{hour}:{mins}".format(hour=str(dt.hour).rjust(2, '0'), mins=str(dt.minute).rjust(2, '0')),
                      f"[dim italic]{row[1]}[/dim italic]")

    console.print(table)
