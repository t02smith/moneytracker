import typer

from rich.console import Console
from rich.table import Table
from rich.progress_bar import ProgressBar

from moneytracker.model import *
from moneytracker.db import *

console = Console()
app = typer.Typer()


@app.command(short_help="Document an expense")
def spend(amount: float, category: str, reason: str):
    insert_expense(Expense(amount, ExpenseCategory[category], reason))


@app.command(short_help="Document a deposit")
def deposit(amount: float, category: str, reason: str):
    insert_expense(Expense(-1 * amount, ExpenseCategory[category], reason))


@app.command(short_help="Gives an overview by category")
def overview():
    res = get_by_categories()

    console.print("[bold magenta]Overview[/bold magenta]!")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Category", width=8)
    table.add_column("Net", width=6)
    table.add_column("Budget", width=25)
    table.add_column("Remaining", width=10)

    def remaining_amount_colour(total: int, leftover: int):
        ratio = leftover/total
        if ratio >= 1:
            return "red1"
        elif ratio >= 0.7:
            return "orange_red1"
        elif ratio >= 0.4:
            return "yellow"
        else:
            return "green"

    for row in res:
        expense_cat = ExpenseCategory[row[0]]
        colour = get_colour_from_category(expense_cat)
        progress = ProgressBar(
            total=row[2],
            completed=row[1] if row[1] < row[2] else row[2],
            width=25
        )
        table.add_row(f"[{colour}]{expense_cat.name}[/{colour}]", "[bold]£{amount:.2f}[/bold]"
                      .format(amount=row[1]), progress,
                      "[bold {colour}]£{amount:.2f}[/bold {colour}]"
                      .format(amount=row[2]-row[1], colour=remaining_amount_colour(row[2], row[1])))

    console.print(table)


@app.command(short_help="Set a budget")
def budget(category: str, amount: float):
    cat = ExpenseCategory[category]
    old = set_budget(cat, amount)
    if old is None:
        console.print("[bold green]Set {category} budget to {amount:.2f}[/bold green]"
                      .format(category=category, amount=amount))
    else:
        if old == amount:
            console.print("Category [bold {colour}]{category}[/bold {colour}] is already [bold red1]"
                          "{amount:.2f}[/bold red1]"
                          .format(category=category, colour=get_colour_from_category(cat), amount=amount))
        else:
            console.print("Updating [bold {colour}]{category}[/bold {colour}] budget from [bold orange]"
                          "{old:.2f}[/bold orange] to [bold green]{new:.2f}[/bold green]"
                          .format(category=category, old=old, new=amount, colour=get_colour_from_category(cat)))
