import unittest

from lifeloop.model import Action, ActionKind, Business, Scenario, replay
from lifeloop.polish import polish


class PolishTests(unittest.TestCase):
    def test_early_refund_rebuy_accelerates_a_later_upgrade(self):
        scenario = Scenario(starting_cash=1000, max_businesses=1, end_month=272)
        businesses = (Business("Small", 1000, 1), Business("Large", 1400, 100))
        seed = replay(scenario, (Action(265, ActionKind.JOB_BOOST), Action(265, ActionKind.BUY, 0),
                                 Action(266, ActionKind.BUSINESS_BOOST), Action(271, ActionKind.SELL, 0),
                                 Action(271, ActionKind.BUY, 1)), businesses)
        result, _ = polish(scenario, seed, 1, businesses)
        self.assertEqual(result.final_cash, 4220)
        self.assertIn(Action(265, ActionKind.REFUND_BOOST, 0), result.actions)
        self.assertIn(Action(265, ActionKind.BUY, 1), result.actions)
        self.assertEqual(replay(scenario, result.actions, businesses), result)

    def test_no_trades_when_custom_scenario_has_no_paid_months(self):
        scenario = Scenario(starting_cash=3000, end_month=265)
        seed = replay(scenario, ())
        result, _ = polish(scenario, seed, 1)
        self.assertEqual(result, seed)

    def test_final_buy_refund_is_immediate_and_adds_40_percent(self):
        scenario = Scenario(starting_cash=1000, max_businesses=1, end_month=266)
        businesses = (Business("Shop", 1000, 1),)
        result, _ = polish(scenario, replay(scenario, (), businesses), 1, businesses)
        self.assertEqual(result.final_cash, 1520)
        self.assertFalse(result.final_sales)
        self.assertEqual(result.actions[-2:], (Action(265, ActionKind.BUY, 0),
                                               Action(265, ActionKind.REFUND_BOOST, 0)))

    def test_refinement_moves_purchases_and_boosts_earlier_when_profitable(self):
        scenario = Scenario(starting_cash=1000, max_businesses=2, end_month=270)
        businesses = (Business("Shop", 100, 100),)
        seed = replay(scenario, (Action(268, ActionKind.JOB_BOOST), Action(269, ActionKind.BUSINESS_BOOST),
                                 Action(269, ActionKind.BUY, 0)), businesses)
        result, stats = polish(scenario, seed, 1, businesses)
        self.assertEqual(result.final_cash, 1000 + 5 * 120 - 100 + 4 * 400 + 140)
        self.assertGreater(result.final_cash, seed.final_cash)
        self.assertEqual(replay(scenario, result.actions, businesses), result)
        self.assertGreater(stats["polish_evaluations"], 0)

    def test_refund_can_move_from_cheap_cycle_to_larger_terminal_sale(self):
        scenario = Scenario(starting_cash=2000, max_businesses=2, end_month=268)
        businesses = (Business("Small", 100, 1), Business("Large", 1000, 1))
        seed = replay(scenario, (Action(265, ActionKind.BUY, 0), Action(265, ActionKind.REFUND_BOOST, 0),
                                 Action(265, ActionKind.BUY, 0), Action(266, ActionKind.BUY, 1)), businesses)
        result, _ = polish(scenario, seed, 1, businesses)
        self.assertGreater(result.final_cash, seed.final_cash)
        self.assertFalse(any(a.kind == ActionKind.REFUND_BOOST for a in result.actions))
        self.assertEqual(result.final_sales[0].kind, ActionKind.REFUND_BOOST)
        self.assertEqual(result.final_sales[0].business, 1)
        self.assertEqual(replay(scenario, result.actions, businesses), result)

    def test_disabled_or_invalid_polish_budget_preserves_incumbent(self):
        scenario = Scenario(end_month=267)
        seed = replay(scenario, ())
        result, stats = polish(scenario, seed, 0)
        self.assertEqual(result, seed)
        self.assertEqual(stats["polish_status"], "disabled")
        for value in (-1, 61, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                polish(scenario, seed, value)
