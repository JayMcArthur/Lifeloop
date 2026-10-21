from contextlib import redirect_stdout
from io import StringIO
import unittest

from lifeloop.model import Action, ActionKind, Education, Scenario, StartingBonus, replay
from main import print_route


class DisplayedDateTimingTests(unittest.TestCase):
    def test_primary_applied_at_12_2_matches_2988_then_3058(self):
        boost = (Action(146, ActionKind.JOB_BOOST),)
        before = replay(Scenario(Education.PRIMARY, StartingBonus.BUSINESS, end_month=228), boost)
        after = replay(Scenario(Education.PRIMARY, StartingBonus.BUSINESS, end_month=229), boost)
        self.assertEqual(before.final_cash, 2988)
        self.assertEqual(after.final_cash, 3058)

    def test_primary_applied_at_12_1_can_afford_green_fork_at_19_0(self):
        result = replay(Scenario(Education.PRIMARY, StartingBonus.BUSINESS, end_month=228),
                        (Action(145, ActionKind.JOB_BOOST),))
        self.assertEqual(result.final_cash, 3006)

    def test_liquidation_precedes_terminal_payment_and_ends_without_business_income(self):
        scenario = Scenario(Education.PRIMARY, StartingBonus.BUSINESS, 3000, end_month=147)
        result = replay(scenario, (Action(144, ActionKind.BUY, 0),))
        self.assertEqual(result.final_sales, (Action(146, ActionKind.REFUND_BOOST, 0),))
        self.assertEqual(result.final_cash, 4200 + 2 * 70 + 3 * 18)

    def test_readable_route_names_application_and_first_boosted_payment(self):
        scenario = Scenario(Education.PRIMARY, StartingBonus.BUSINESS)
        result = replay(scenario, (Action(145, ActionKind.JOB_BOOST),))
        output = StringIO()
        with redirect_stdout(output):
            print_route(scenario, result)
        self.assertIn('12y01m: apply job boost', output.getvalue())
        self.assertIn('first payment 12y02m', output.getvalue())
        self.assertIn('last payment 22y01m', output.getvalue())


if __name__ == '__main__':
    unittest.main()
