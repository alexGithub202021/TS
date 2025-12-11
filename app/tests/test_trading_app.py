# units test 'cases'

"""

1/ basic op:
    buy
    sell
    short sell
    close short sell

        => mock
            kraken/bin api
            redis
            csv

2/ others:
    price update after buy order
    price update after sell order

    sell order before price update
    close short sell order before price update

    sell order after price update
    close short sell order after price update

to implement:
    stop transactions after daily benefit reach a certain level (secure benefit)
    stop transactions after daily loss reach a certain level (stop loss -> analyse)
    change automatically threesholds n paces n number_changes_direction_allowed / avg daily changes n cur period (use historic)

"""

import unittest
from unittest.mock import MagicMock, patch
from util.trading_app import Trading_app


class Trading_app_test(unittest.TestCase):

    def setUp(self):
        self.app = Trading_app()  # Create an instance of the User class
        self.mock_cursor = MagicMock()  # Create a mock cursor
        self.app.cursor = self.mock_cursor  # Set the mock cursor for the User instance

    def test_buy_order(self):
        self.assertEqual(True, False)

    def test_sell_order(self):
        self.assertEqual(True, True)

    def test_short_sell_order(self):
        self.assertEqual(True, True)

    def test_close_short_sell_order(self):
        self.assertEqual(True, True)

    def test_price_update_after_buy_order(self):
        self.assertEqual(True, True)

    def test_price_update_after_sell_order(self):
        self.assertEqual(True, True)

    def test_sell_order_before_price_change(self):
        self.assertEqual(True, True)

    def test_close_short_sell_order_before_price_change(self):
        self.assertEqual(True, True)

    def test_sell_order_after_price_change(self):
        self.assertEqual(True, True)

    def test_close_short_sell_order_after_price_change(self):
        self.assertEqual(True, True)


if __name__ == "__main__":
    unittest.main()


# # example of a test case
# Define a function to be tested
# def add(a, b):
#     return a + b

# # Define a test case class that inherits from unittest.TestCase
# class TestAddFunction(unittest.TestCase):

#     # Define a test method that starts with 'test_'
#     def test_add_positive_numbers(self):
#         self.assertEqual(add(2, 3), 5)  # Test that 2 + 3 equals 5
#         # self.assertEqual(add(2, 3), 4)
# if __name__ == '__main__':
#     unittest.main()
