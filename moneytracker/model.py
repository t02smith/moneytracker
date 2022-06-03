from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime, timedelta


class ExpenseCategory(Enum):
    """
    Represents different expense categories
    Each category should give contextual information about what an expense
    is without the need to read the reason
    """
    UTILITY = auto()  # rent, water, gas & electric, ...
    FOOD = auto()  # food items: shopping, meals out, ...
    HAZARD = auto()  # repairs or unexpected expenses
    TREAT = auto()  # treat items: cinema tickets, video games, ...
    WAGE = auto()  # wage income
    GIFT = auto()  # gift items
    GENERAL = auto()

    def description(self):
        match self:
            case ExpenseCategory.UTILITY: return "Money spent on bills (e.g. rent, water, gas, ...)"
            case ExpenseCategory.FOOD: return "Money spent on food including going out to eat"
            case ExpenseCategory.HAZARD: return "Unexpected payments for repairs or emergency costs"
            case ExpenseCategory.TREAT: return "Unnecessary purchases as a treat to yourself"
            case ExpenseCategory.WAGE: return "Income from employment or expense for employees"
            case ExpenseCategory.GIFT: return "Gifts for other people (e.g. birthdays)"


class TimeFrame(Enum):
    """
    Used to specify the time frame in which a budget exists for
    Expenses are only counted if they are within the time frame
    """
    DAY = 1  # Last 24hrs
    WEEK = 7  # Last 7 days
    MONTH = 28  # Last 28 days
    YEAR = 365  # Last 365 days
    FOREVER = -1  # No time frame limit


def get_colour_from_category(cat: ExpenseCategory):
    """
    Maps an expense category to a colour from rich
    :param cat: The category
    :return: The rich colour
    """
    colours = ["cyan", "green", "red1", "orange_red1", "hot_pink", "purple", "yellow1"]
    return colours[cat.value % len(colours)]


@dataclass
class Expense:
    amount: float
    category: ExpenseCategory
    reason: str
    date: datetime
    account: int

    def __hash__(self):
        return hash((self.amount, self.category, self.reason, datetime.now()))


@dataclass
class Budget:
    amount: float
    category: ExpenseCategory
    time_frame: TimeFrame


def is_within_time_frame(tf: TimeFrame, dt: datetime):
    delta = datetime.now() - dt
    return True if tf is TimeFrame.FOREVER else not delta.days > tf.value


def oldest_time(tf: TimeFrame):
    now = datetime.now()
    if tf is TimeFrame.FOREVER:
        return now - now

    return now - timedelta(tf.value)
