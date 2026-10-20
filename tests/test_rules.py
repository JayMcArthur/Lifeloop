import unittest

from lifeloop.model import (
    BOOST_MONTHS, BUSINESSES, JOBS, MAX_BUSINESSES, Action, ActionKind,
    Business, Education, Scenario, StartingBonus, State, activate, finish,
    income, job_payment, replay, trade,
)
from lifeloop.solver import solve


class GameRulesTests(unittest.TestCase):
    def test_education_sets_start_age_and_first_payment(self):
        for education, years, first_pay in (
            (Education.SUNNY_SPROUT, 10, 10),
            (Education.FRESHMART, 12, 18),
            (Education.BRICKLINE, 17, 25),
            (Education.BYTEFIX, 19, 45),
            (Education.DOCUDYNO, 22, 60),
        ):
            with self.subTest(education=education):
                self.assertEqual(education.start_month, years * 12)
                self.assertEqual(job_payment(education, years * 12), 0)
                self.assertEqual(job_payment(education, years * 12 + 1), first_pay)

    def test_upgrades_pay_the_following_month(self):
        for education, (_, schedule) in JOBS.items():
            for index in range(1, len(schedule)):
                tenure, payment = schedule[index]
                upgrade = education.start_month + tenure
                with self.subTest(education=education, upgrade=upgrade):
                    self.assertEqual(job_payment(education, upgrade), schedule[index - 1][1])
                    self.assertEqual(job_payment(education, upgrade + 1), payment)
        self.assertEqual(job_payment(Education.DOCUDYNO, 71 * 12 + 6), 300)
        self.assertEqual(job_payment(Education.DOCUDYNO, 71 * 12 + 7), 400)

    def test_business_catalog_and_round_limits(self):
        self.assertEqual(len(BUSINESSES), 16)
        self.assertEqual(BUSINESSES[0], Business("Green Fork", 3_000, 35))
        self.assertEqual(BUSINESSES[-1], Business("Bright Core", 13_790_000, 35_500))
        self.assertEqual(Scenario().end_month, 90 * 12)
        self.assertEqual(Scenario().max_businesses, MAX_BUSINESSES)
        self.assertEqual(MAX_BUSINESSES, 9)

    def test_starting_bonus_doubles_only_selected_income(self):
        state = State(owned=(0,))
        month = Education.DOCUDYNO.start_month + 1
        job = Scenario(starting_bonus=StartingBonus.JOB)
        business = Scenario(starting_bonus=StartingBonus.BUSINESS)
        self.assertEqual(income(job, state, month), 60 * 2 + 35)
        self.assertEqual(income(business, state, month), 60 + 35 * 2)

    def test_independent_boosts_stack_for_exactly_120_payments(self):
        for bonus in StartingBonus:
            scenario = Scenario(starting_bonus=bonus)
            start = 75 * 12
            state = State(owned=(0,))
            state = activate(state, Action(start, ActionKind.JOB_BOOST))
            state = activate(state, Action(start + 5, ActionKind.BUSINESS_BOOST))
            job = 400 * scenario.job_multiplier
            business = 35 * scenario.business_multiplier
            with self.subTest(bonus=bonus):
                self.assertEqual(income(scenario, state, start + 5), job * 2 + business * 2)
                self.assertEqual(income(scenario, state, start + 119), job * 2 + business * 2)
                self.assertEqual(income(scenario, state, start + 120), job + business * 2)
                self.assertEqual(income(scenario, state, start + 125), job + business)
        self.assertEqual(BOOST_MONTHS, 120)

    def test_expired_income_boost_cannot_be_reused(self):
        for kind in (ActionKind.JOB_BOOST, ActionKind.BUSINESS_BOOST):
            state = activate(State(), Action(300, kind))
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "already been used"):
                activate(state, Action(500, kind))

    def test_ninth_purchase_allowed_tenth_rejected(self):
        scenario = Scenario()
        state = State(cash=6_000, owned=(0,) * 8)
        state = trade(scenario, state, Action(300, ActionKind.BUY, 0))
        self.assertEqual(len(state.owned), 9)
        with self.assertRaisesRegex(ValueError, "No free business slot"):
            trade(scenario, state, Action(300, ActionKind.BUY, 0))

    def test_140_percent_refund_applies_to_one_copy_once(self):
        scenario = Scenario()
        state = State(owned=(0, 0))
        state = trade(scenario, state, Action(300, ActionKind.REFUND_BOOST, 0))
        self.assertEqual(state.cash, 4_200)
        self.assertEqual(state.owned, (0,))
        with self.assertRaisesRegex(ValueError, "already been used"):
            trade(scenario, state, Action(301, ActionKind.REFUND_BOOST, 0))
        state = trade(scenario, state, Action(301, ActionKind.SELL, 0))
        self.assertEqual(state.cash, 6_300)
        self.assertEqual(state.owned, ())

    def test_unused_refund_boost_only_applies_to_largest_final_sale(self):
        scenario = Scenario()
        result = finish(scenario, State(cash=100, owned=(0, 1)), ())
        self.assertEqual(result.final_cash, 100 + 8_400 + 2_100)
        self.assertEqual(sum(a.kind == ActionKind.REFUND_BOOST for a in result.final_sales), 1)
        self.assertEqual(result.final_sales[0].business, 1)
        used = finish(scenario, State(owned=(0, 1), refund_used=True), ())
        self.assertEqual(used.final_cash, 2_100 + 4_200)

    def test_replay_has_no_income_on_purchase_or_terminal_month(self):
        first = Education.DOCUDYNO.start_month + 1
        scenario = Scenario(starting_cash=3_000, end_month=first + 2)
        result = replay(scenario, (Action(first, ActionKind.BUY, 0),))
        self.assertEqual(result.final_cash, 60 + 60 + 70 + 4_200)

    def test_replay_applies_boost_before_current_month_payment(self):
        first = Education.DOCUDYNO.start_month + 1
        scenario = Scenario(starting_bonus=StartingBonus.JOB, end_month=first + 1)
        result = replay(scenario, (Action(first, ActionKind.JOB_BOOST),))
        self.assertEqual(result.final_cash, 60 * 4)

    def test_full_boost_window_spans_a_pay_upgrade_then_expires(self):
        first = Education.DOCUDYNO.start_month + 1
        scenario = Scenario(starting_bonus=StartingBonus.JOB, end_month=first + 125)
        result = replay(scenario, (Action(first, ActionKind.JOB_BOOST),))
        permanent_income = 2 * (78 * 60 + 47 * 100)
        boost_income = 2 * (78 * 60 + 42 * 100)
        self.assertEqual(result.final_cash, permanent_income + boost_income)

    def test_boost_is_clipped_at_end_of_round(self):
        scenario = Scenario(starting_cash=3_000)
        first = scenario.end_month - 3
        # Starting late never grants payments beyond the round's horizon.
        actions = (Action(first, ActionKind.BUY, 0),
                   Action(first + 1, ActionKind.BUSINESS_BOOST))
        boosted = replay(scenario, actions)
        ordinary = replay(scenario, (actions[0],))
        self.assertEqual(boosted.final_cash - ordinary.final_cash, 2 * 35 * 2)

    def test_replay_rejects_boost_after_trading_and_outside_round(self):
        first = Education.DOCUDYNO.start_month + 1
        scenario = Scenario(starting_cash=3_000)
        with self.assertRaisesRegex(ValueError, "before the month's trades"):
            replay(scenario, (Action(first, ActionKind.BUY, 0), Action(first, ActionKind.JOB_BOOST)))
        with self.assertRaisesRegex(ValueError, "inside the round"):
            replay(scenario, (Action(scenario.end_month, ActionKind.JOB_BOOST),))

    def test_trades_require_cash_and_ownership(self):
        with self.assertRaisesRegex(ValueError, "Cannot afford"):
            trade(Scenario(), State(), Action(300, ActionKind.BUY, 0))
        with self.assertRaisesRegex(ValueError, "unowned"):
            trade(Scenario(), State(), Action(300, ActionKind.SELL, 0))

    def test_search_finds_known_short_round_best_and_replays(self):
        first = Education.DOCUDYNO.start_month + 1
        businesses = (Business("Test shop", 100, 20),)
        scenario = Scenario(starting_cash=100, max_businesses=1, end_month=first + 4)
        result = solve(scenario, beam_width=256, businesses=businesses).result
        # Four boosted job payments, three boosted shop payments, one final 140% refund.
        self.assertEqual(result.final_cash, 4 * 120 + 3 * 80 + 140)
        self.assertEqual(replay(scenario, result.actions, businesses), result)

    def test_search_replays_for_every_education_and_starting_bonus(self):
        businesses = (Business("Small", 100, 20), Business("Large", 200, 40))
        for education in Education:
            for bonus in StartingBonus:
                with self.subTest(education=education, bonus=bonus):
                    scenario = Scenario(education, bonus, 100, 2, education.start_month + 7)
                    result = solve(scenario, 32, businesses).result
                    self.assertEqual(replay(scenario, result.actions, businesses), result)

    def test_empty_portfolio_can_finish_without_refund_boost(self):
        first = Education.SUNNY_SPROUT.start_month + 1
        scenario = Scenario(Education.SUNNY_SPROUT, StartingBonus.JOB, end_month=first + 2)
        result = solve(scenario, 8).result
        self.assertEqual(result.final_cash, 2 * 10 * 4)
        self.assertEqual(result.final_sales, ())


if __name__ == "__main__":
    unittest.main()
