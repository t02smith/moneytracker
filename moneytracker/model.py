from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime


class ExpenseCategory(Enum):
    UTILITY = auto()  # rent, water, gas & electric, ...
    FOOD = auto()  # food items: shopping, meals out, ...
    HAZARD = auto()  # repairs or unexpected expenses
    TREAT = auto()  # treat items: cinema tickets, video games, ...
    WAGE = auto()  # wage income
    GIFT = auto()  # gift items

    def description(self):
        match self:
            case ExpenseCategory.UTILITY: return "Money spent on bills (e.g. rent, water, gas, ...)"
            case ExpenseCategory.FOOD: return "Money spent on food including going out to eat"
            case ExpenseCategory.HAZARD: return "Unexpected payments for repairs or emergency costs"
            case ExpenseCategory.TREAT: return "Unnecessary purchases as a treat to yourself"
            case ExpenseCategory.WAGE: return "Income from employment or expense for employees"
            case ExpenseCategory.GIFT: return "Gifts for other people (e.g. birthdays)"


def get_colour_from_category(cat: ExpenseCategory):
    colours = ["cyan", "green", "red1", "orange_red1", "pink", "purple"]
    return colours[cat.value % len(colours)]


@dataclass
class Expense:
    amount: float
    category: ExpenseCategory
    reason: str

    def __hash__(self):
        return hash((self.amount, self.category, self.reason, datetime.now()))
