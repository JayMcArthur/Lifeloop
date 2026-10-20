from math import ceil
from enum import IntEnum
from typing import List, Tuple
from functools import lru_cache


class Date:
    def __init__(self, months: int|float):
        self.internal:int = ceil(months)
        self.year:int = 0
        self.month:int = 0
        self._recalculate()

    def _recalculate(self):
        self.year:int = self.internal // 12
        self.month:int = self.internal % 12

    def __str__(self):
        return f"{self.year}·{self.month:02}T"
    def __repr__(self):
        return f"{type(self).__name__}({self.internal=}, {self.year=}, {self.month=})"
    def __eq__(self, other):
        return self.internal == other.internal
    def __lt__(self, other):
        return self.internal < other.internal
    def __gt__(self, other):
        return self.internal > other.internal
    def __le__(self, other):
        return self.internal <= other.internal
    def __ge__(self, other):
        return self.internal >= other.internal
    def __add__(self, other):
        return Date(self.internal + other.internal)
    def __sub__(self, other):
        return Date(self.internal - other.internal)

class Business:
    def __init__(self, name: str, cost: int, earn: int, sale: int=0.7):
        self.name:str = name
        self.cost = cost * 1000
        self.earn = earn
        self.sale = sale
    def __str__(self):
        return f"{self.name}: {self.break_even(2)}"
    def effective_roi(self, time_remaining:Date):
        return (time_remaining.internal * self.cost) / (self.cost * 0.3)
    def break_even(self, business_bonus:float):
        return Date(ceil((self.cost * (1 - self.sale)) / (self.earn * business_bonus)))

class JobTypes(IntEnum):
    SunnySproutFields = 0
    FreshMart = 1
    BrickLineWorks = 2
    ByteFixServices = 3
    DocuDynoCorp = 4

def work_earning(job: JobTypes, date: Date):
    earnings = [
        [{'start': Date(0), 'earn': 10}, {'start': Date(12*8), 'earn': 20}, {'start': Date(12*17), 'earn': 35}, {'start': Date(12*27), 'earn': 55}, {'start': Date(12*40), 'earn': 80}],
        [{'start': Date(0), 'earn': 18}, {'start': Date(12*7), 'earn': 35}, {'start': Date(12*15), 'earn': 60}, {'start': Date(12*25), 'earn': 90}, {'start': Date(12*38), 'earn': 140}],
        [{'start': Date(0), 'earn': 25}, {'start': Date(12*7), 'earn': 45}, {'start': Date(12*15), 'earn': 75}, {'start': Date(12*25), 'earn': 110}, {'start': Date(12*38), 'earn': 170}],
        [{'start': Date(0), 'earn': 45}, {'start': Date(12*6+6), 'earn': 75}, {'start': Date(12*13+6), 'earn': 110}, {'start': Date(12*22+6), 'earn': 165}, {'start': Date(12*33+6), 'earn': 240}, {'start': Date(12*47+6), 'earn': 320}],
        [{'start': Date(0), 'earn': 60}, {'start': Date(12*6+6), 'earn': 100}, {'start': Date(12*13+6), 'earn': 150}, {'start': Date(12*22+6), 'earn': 220}, {'start': Date(12*34+6), 'earn': 300}, {'start': Date(12*49+6), 'earn': 400}]
    ]

    for earning in reversed(earnings[job]):
        if earning['start'] <= date:
            return earning['earn']
    return None

def work_start_date(job: JobTypes):
    match job:
        case JobTypes.SunnySproutFields:
            return Date(12 * 10)
        case JobTypes.FreshMart:
            return Date(12 * 12)
        case JobTypes.BrickLineWorks:
            return Date(12 * 17)
        case JobTypes.ByteFixServices:
            return Date(12 * 19)
        case JobTypes.DocuDynoCorp:
            return Date(12 * 22)

def compress_earning(lst):
    if not lst:
        return []

    result = []
    current = lst[0]
    count = 1

    for val in lst[1:]:
        if val == current:
            count += 1
        else:
            result.append(f"${current} x{count}" if count > 1 else f"${current}")
            current = val
            count = 1

    result.append(f"${current} x{count}" if count > 1 else f"${current}")
    return result

class Person:
    def __init__(self, name: str):
        self.name = name
        self.business_slots = 5
        self.businesses:list[Business]=[]

all_businesses = [
    Business(name="Green Fork", cost=3, earn=35),
    Business(name="Cup & Go", cost=6, earn=56),
    Business(name="Spark Fix", cost=12, earn=90),
    Business(name="Pedal Fleet", cost=24, earn=143),
    Business(name="Tech Tinker", cost=43, earn=230),
    Business(name="Trend Loop", cost=78, earn=370),
    Business(name="Paw Pal", cost=140, earn=590),
    Business(name="Dash Logix", cost=252, earn=940),
    Business(name="Crust & Crumb", cost=428, earn=1_500),
    Business(name="Tailor Forge", cost=728, earn=2_400),
    Business(name="Skysoft", cost=1_238, earn=3_850),
    Business(name="Rapid Reach", cost=2_104, earn=6_150),
    Business(name="Agri World", cost=3_367, earn=9_500),
    Business(name="Globe Freight", cost=5_387, earn=15_000),
    Business(name="Data Vault", cost=8_619, earn=23_000),
    Business(name="Bright Core", cost=13_790, earn=35_500)
]

def optimize_investments(
    businesses: list[Business],
    job: JobTypes,
    job_bonus: float,
    business_bonus: float,
    start_date: Date,
    end_date: Date,
    starting_cash: int,
    max_businesses: int,
    wait_months_threshold: int = 30,
    min_upgrade_ratio: float = 1.6  # 1.6 - 3.0 > $6,640,776
):
    current_date = Date(start_date.internal + 1)
    cash = starting_cash
    owned = []
    history = []
    save_target = None  # Track if we're saving for something

    while current_date < end_date:
        job_income = work_earning(job, current_date - work_start_date(job) - Date(1)) * job_bonus
        business_income = sum(b.earn for b in owned) * business_bonus
        total_income = job_income + business_income
        cash += total_income

        months_left = end_date.internal - current_date.internal

        # If we're in save mode
        if save_target:
            if cash >= save_target.cost:
                owned.append(save_target)
                cash -= save_target.cost
                history.append((Date(current_date.internal), f"Bought {save_target.name} (saved up)"))
                save_target = None
            else:
                # history.append((Date(current_date.internal), f"Waiting to afford {save_target.name}"))
                current_date += Date(1)
                continue

        # Evaluate all viable business options
        viable = [
            (b, (months_left - b.break_even(business_bonus).internal) * b.earn - b.cost * 0.3)
            for b in businesses
            if (months_left - b.break_even(business_bonus).internal) > 0
        ]
        viable.sort(key=lambda x: x[1], reverse=True)

        made_change = False

        for b, _ in viable:
            # Skip upgrades that don't meaningfully increase income
            if len(owned) == max_businesses:
                worst = min(owned, key=lambda x: x.earn)
                if b.earn <= worst.earn * (1 + min_upgrade_ratio):
                    continue

            # Buy new if we have room
            if len(owned) < max_businesses and cash >= b.cost:
                owned.append(b)
                cash -= b.cost
                history.append((Date(current_date.internal), f"Bought {b.name}"))
                made_change = True
                break

            # Swap existing if profitable
            elif len(owned) == max_businesses:
                worst = min(owned, key=lambda x: x.earn)
                if b.earn > worst.earn and cash + worst.cost * 0.7 >= b.cost:
                    owned.remove(worst)
                    cash += worst.cost * 0.7
                    cash -= b.cost
                    owned.append(b)
                    history.append((Date(current_date.internal), f"Swapped {worst.name} → {b.name}"))
                    made_change = True
                    break

        # If nothing was done and we have open slots, consider saving
        if not made_change and len(owned) < max_businesses:
            for b in businesses[::-1]:  # Start with most expensive
                if (months_left - b.break_even(business_bonus).internal) > 0 and cash < b.cost:
                    if total_income > 0:
                        wait_months = int(ceil((b.cost - cash) / total_income))
                        if wait_months <= wait_months_threshold:
                            save_target = b
                            # history.append((Date(current_date.internal), f"Begin saving for {b.name}"))
                            break

        current_date += Date(1)

    # Final sell-off
    cash += sum(b.cost * 0.7 for b in owned)
    return cash, history



class DFSOptimizer:
    def __init__(self, businesses: List[Business], job: JobTypes, job_bonus: float, business_bonus: float):
        self.businesses = businesses
        self.job = job
        self.job_bonus = job_bonus
        self.business_bonus = business_bonus
        self.start = work_start_date(job)
        self.end = Date(12 * 90)
        self.max_month = self.end.internal
        self.max_slots = 5
        self.bucket_multiple = 1000
        self.bucket_min = 3000
        self.name_to_business = {b.name: b for b in businesses}

    def job_income(self, month: int) -> int:
        job_month = Date(month) - self.start - Date(1)
        return int(work_earning(self.job, job_month) * self.job_bonus)

    def bucket(self, cash: int) -> int:
        return (cash // self.bucket_multiple) * self.bucket_multiple if cash >= self.bucket_min else 0

    def run(self) -> Tuple[int, Tuple[Tuple[int, str]]]:
        return self._dfs(
            month=self.start.internal + 1,
            bucketed_cash=0,
            owned=tuple(),
            cash=0
        )

    @lru_cache(maxsize=5_000_000)
    def _dfs(self, month: int, bucketed_cash: int, owned: Tuple[str], cash: int) -> Tuple[int, Tuple[Tuple[int, str]]]:
        if month >= self.max_month:
            resale = sum(self.name_to_business[name].cost * 0.7 for name in owned)
            return int(cash + resale), ()

        # Income this month
        income = self.job_income(month) + (sum(self.name_to_business[name].earn for name in owned) * self.business_bonus)
        new_cash = cash + income
        new_bucket = self.bucket(new_cash)

        # Option 1: Wait
        best_value, best_history = self._dfs(
            month + 1,
            new_bucket,
            tuple(sorted(owned)),
            new_cash
        )

        # Option 2: Buy (if slots available)
        if len(owned) < self.max_slots:
            for b in self.businesses:
                if new_cash >= b.cost:
                    updated_owned = tuple(sorted(owned + (b.name,)))
                    value, path = self._dfs(
                        month + 1,
                        self.bucket(new_cash - b.cost),
                        updated_owned,
                        new_cash - b.cost
                    )
                    if value > best_value:
                        best_value = value
                        best_history = ((month, f"Buy {b.name}"),) + path

        # Option 3: Swap (if full)
        if len(owned) == self.max_slots:
            for b in self.businesses:
                for i, w_name in enumerate(owned):
                    w = self.name_to_business[w_name]
                    if b.earn > w.earn:
                        gained = int(w.cost * 0.7)
                        if new_cash + gained >= b.cost:
                            new_owned = list(owned)
                            new_owned[i] = b.name
                            value, path = self._dfs(
                                month + 1,
                                self.bucket(new_cash + gained - b.cost),
                                tuple(sorted(new_owned)),
                                new_cash + gained - b.cost
                            )
                            if value > best_value:
                                best_value = value
                                best_history = ((month, f"Swap {w.name} → {b.name}"),) + path

        return best_value, best_history


def print_lifetime_earning():
    # Lifetime profits for jobs
    for job in JobTypes:
        all_dates = [Date(i) for i in range((90 - work_start_date(job).year) * 12 - 1)]
        earnings = [work_earning(job, d) * job_bonus for d in all_dates]
        print(f"{job.name:>17}: ${sum(earnings):>7,} - {compress_earning(earnings)}")

def print_break_even():
    # When Business breaks even
    for business in all_businesses:
        print(business)

def find_best_greedy_config(
    businesses: list[Business],
    job: JobTypes,
    job_bonus: float,
    business_bonus: float,
    start_date: Date,
    end_date: Date,
    starting_cash: int,
    max_businesses: int,
    wait_options: list[int],
    upgrade_options: list[float]
):
    best_result = {
        "final_cash": 0,
        "wait_months_threshold": None,
        "min_upgrade_ratio": None,
        "history": None
    }

    for wait in wait_options:
        for upgrade in upgrade_options:
            final_cash, history = optimize_investments(
                businesses=businesses,
                job=job,
                job_bonus=job_bonus,
                business_bonus=business_bonus,
                start_date=start_date,
                end_date=end_date,
                starting_cash=starting_cash,
                max_businesses=max_businesses,
                wait_months_threshold=wait,
                min_upgrade_ratio=upgrade
            )

            print(f"Wait={wait:2d}, Upgrade={upgrade:.2f} → Final Cash=${final_cash:,.0f}")

            if final_cash > best_result["final_cash"]:
                best_result.update({
                    "final_cash": final_cash,
                    "wait_months_threshold": wait,
                    "min_upgrade_ratio": upgrade,
                    "history": history
                })

    return best_result




if __name__ == "__main__":
    # import time

    # optimizer = DFSOptimizer(
    #     businesses=all_businesses,
    #     job=JobTypes.DocuDynoCorp,
    #     job_bonus=1.75
    # )

    # start_time = time.time()
    # final_value, path = optimizer.run()
    # end_time = time.time()

    # print(f"Final value at age 90: ${final_value:,}")
    # print(f"Took {end_time - start_time:.2f} seconds\n")
    # for month, action in path:
    #     print(f"{Date(month)}: {action}")

    job = JobTypes.FreshMart

    result = find_best_greedy_config(
        businesses=all_businesses,
        job=job,
        job_bonus=1,
        business_bonus=2,
        start_date=work_start_date(job),
        end_date=Date(12 * 90),
        starting_cash=0,
        max_businesses=7,
        wait_options= [i*3 for i in range(11)],
        upgrade_options= [0.01*i for i in range(251)]
    )

    for m, action in result["history"]:
        print(f"{m}: {action}")

    print(f"\n🏆 Best Final Cash: ${result['final_cash']:,.0f}")
    print(f"Wait Months: {result['wait_months_threshold']}, Min Upgrade Ratio: {result['min_upgrade_ratio']}")

    # print_break_even()
    # print_lifetime_earning()



# 12,372,066
