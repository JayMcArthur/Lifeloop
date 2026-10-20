"""Monthly game rules and deterministic strategy replay."""

from dataclasses import dataclass, replace
from enum import Enum
from itertools import groupby


BOOST_MONTHS = 120
MAX_BUSINESSES = 9
END_MONTH = 90 * 12


class Education(Enum):
    SUNNY_SPROUT = "sunny-sprout"
    FRESHMART = "freshmart"
    BRICKLINE = "brickline"
    BYTEFIX = "bytefix"
    DOCUDYNO = "docudyno"

    @property
    def start_month(self) -> int:
        return JOBS[self][0] * 12


# Each threshold is tenure at the upgrade. Its new pay arrives next month.
JOBS = {
    Education.SUNNY_SPROUT: (10, ((0, 10), (96, 20), (204, 35), (324, 55), (480, 80))),
    Education.FRESHMART: (12, ((0, 18), (84, 35), (180, 60), (300, 90), (456, 140))),
    Education.BRICKLINE: (17, ((0, 25), (84, 45), (180, 75), (300, 110), (456, 170))),
    Education.BYTEFIX: (19, ((0, 45), (78, 75), (162, 110), (270, 165), (402, 240), (570, 320))),
    Education.DOCUDYNO: (22, ((0, 60), (78, 100), (162, 150), (270, 220), (414, 300), (594, 400))),
}


class StartingBonus(Enum):
    JOB = "job"
    BUSINESS = "business"


@dataclass(frozen=True, slots=True)
class Business:
    name: str
    cost: int
    income: int

    def refund(self, boosted: bool = False) -> int:
        # Catalog prices are whole thousands, so both refunds are exact dollars.
        return self.cost * (140 if boosted else 70) // 100


BUSINESSES = (
    Business("Green Fork", 3_000, 35),
    Business("Cup & Go", 6_000, 56),
    Business("Spark Fix", 12_000, 90),
    Business("Pedal Fleet", 24_000, 143),
    Business("Tech Tinker", 43_000, 230),
    Business("Trend Loop", 78_000, 370),
    Business("Paw Pal", 140_000, 590),
    Business("Dash Logix", 252_000, 940),
    Business("Crust & Crumb", 428_000, 1_500),
    Business("Tailor Forge", 728_000, 2_400),
    Business("Skysoft", 1_238_000, 3_850),
    Business("Rapid Reach", 2_104_000, 6_150),
    Business("Agri World", 3_367_000, 9_500),
    Business("Globe Freight", 5_387_000, 15_000),
    Business("Data Vault", 8_619_000, 23_000),
    Business("Bright Core", 13_790_000, 35_500),
)


@dataclass(frozen=True, slots=True)
class Scenario:
    education: Education = Education.DOCUDYNO
    starting_bonus: StartingBonus = StartingBonus.BUSINESS
    starting_cash: int = 0
    max_businesses: int = MAX_BUSINESSES
    end_month: int = END_MONTH

    def __post_init__(self):
        if not 1 <= self.max_businesses <= MAX_BUSINESSES:
            raise ValueError("A round allows between one and nine business slots")
        if self.end_month <= self.education.start_month:
            raise ValueError("The round must end after education finishes")
        if self.starting_cash < 0:
            raise ValueError("Starting cash cannot be negative")

    @property
    def job_multiplier(self) -> int:
        return 2 if self.starting_bonus == StartingBonus.JOB else 1

    @property
    def business_multiplier(self) -> int:
        return 2 if self.starting_bonus == StartingBonus.BUSINESS else 1


class ActionKind(Enum):
    JOB_BOOST = "job boost"
    BUSINESS_BOOST = "business boost"
    BUY = "buy"
    SELL = "sell (70%)"
    REFUND_BOOST = "sell (140%)"


INCOME_BOOSTS = (ActionKind.JOB_BOOST, ActionKind.BUSINESS_BOOST)


@dataclass(frozen=True, slots=True)
class Action:
    month: int
    kind: ActionKind
    business: int | None = None


@dataclass(frozen=True, slots=True)
class State:
    cash: int = 0
    owned: tuple[int, ...] = ()
    job_until: int = 0
    business_until: int = 0
    refund_used: bool = False


@dataclass(frozen=True, slots=True)
class Result:
    final_cash: int
    actions: tuple[Action, ...]
    final_sales: tuple[Action, ...]


def age(month: int) -> str:
    years, months = divmod(month, 12)
    return f"{years}y{months:02}m"


def job_payment(education: Education, month: int) -> int:
    tenure = month - education.start_month - 1
    for threshold, payment in reversed(JOBS[education][1]):
        if tenure >= threshold:
            return payment
    return 0


def activate(state: State, action: Action) -> State:
    field = "job_until" if action.kind == ActionKind.JOB_BOOST else "business_until"
    if action.kind not in INCOME_BOOSTS:
        raise ValueError("Expected an income boost")
    if getattr(state, field):
        raise ValueError(f"{action.kind.value} has already been used this round")
    return replace(state, **{field: action.month + BOOST_MONTHS})


def income(scenario: Scenario, state: State, month: int, businesses=BUSINESSES) -> int:
    job = job_payment(scenario.education, month) * scenario.job_multiplier
    business = sum(businesses[i].income for i in state.owned) * scenario.business_multiplier
    return job * (2 if month < state.job_until else 1) + business * (2 if month < state.business_until else 1)


def trade(scenario: Scenario, state: State, action: Action, businesses=BUSINESSES) -> State:
    index = action.business
    if index is None or not 0 <= index < len(businesses):
        raise ValueError("Trade must identify a business in the catalog")
    business = businesses[index]
    if action.kind == ActionKind.BUY:
        if len(state.owned) >= scenario.max_businesses:
            raise ValueError("No free business slot")
        if state.cash < business.cost:
            raise ValueError("Cannot afford this business")
        return replace(state, cash=state.cash - business.cost, owned=tuple(sorted((*state.owned, index))))
    if action.kind not in (ActionKind.SELL, ActionKind.REFUND_BOOST):
        raise ValueError("Expected a purchase or sale")
    if index not in state.owned:
        raise ValueError("Cannot sell an unowned business")
    boosted = action.kind == ActionKind.REFUND_BOOST
    if boosted and state.refund_used:
        raise ValueError("Refund boost has already been used this round")
    owned = list(state.owned)
    owned.remove(index)
    return replace(state, cash=state.cash + business.refund(boosted), owned=tuple(owned),
                   refund_used=state.refund_used or boosted)


def finish(scenario: Scenario, state: State, actions: tuple[Action, ...], businesses=BUSINESSES) -> Result:
    sales = []
    if state.owned and not state.refund_used:
        index = max(state.owned, key=lambda i: businesses[i].cost)
        action = Action(scenario.end_month, ActionKind.REFUND_BOOST, index)
        state = trade(scenario, state, action, businesses)
        sales.append(action)
    for index in state.owned:
        action = Action(scenario.end_month, ActionKind.SELL, index)
        state = trade(scenario, state, action, businesses)
        sales.append(action)
    return Result(state.cash, actions, tuple(sales))


def replay(scenario: Scenario, actions: tuple[Action, ...], businesses=BUSINESSES) -> Result:
    """Activate boosts before payment, then trade after payment each month."""
    first_month = scenario.education.start_month + 1
    if any(a.month < first_month or a.month >= scenario.end_month for a in actions):
        raise ValueError("Actions must fall inside the round's paid months")
    if any(a.month > b.month for a, b in zip(actions, actions[1:])):
        raise ValueError("Actions must be ordered by month")
    monthly = {month: tuple(group) for month, group in groupby(actions, key=lambda a: a.month)}
    state = State(cash=scenario.starting_cash)
    for month in range(first_month, scenario.end_month):
        events = monthly.get(month, ())
        trading = False
        for action in events:
            if action.kind in INCOME_BOOSTS:
                if trading:
                    raise ValueError("Income boosts activate before the month's trades")
                state = activate(state, action)
            else:
                trading = True
        state = replace(state, cash=state.cash + income(scenario, state, month, businesses))
        for action in events:
            if action.kind not in INCOME_BOOSTS:
                state = trade(scenario, state, action, businesses)
    return finish(scenario, state, actions, businesses)
