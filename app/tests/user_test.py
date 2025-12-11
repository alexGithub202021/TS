import unittest
from unittest.mock import MagicMock, patch
from controller.user import User  # Import the User class from your module


class TestUser(unittest.TestCase):
    def setUp(self):
        self.user = User()  # Create an instance of the User class
        self.mock_cursor = MagicMock()  # Create a mock cursor
        self.user.cursor = self.mock_cursor  # Set the mock cursor for the User instance

    def test_get_users(self):
        # Mock the results of the query
        mock_results = [
            ("user1", "email1@example.com"),
            ("user2", "email2@example.com"),
        ]
        self.mock_cursor.fetchall.return_value = mock_results

        # Call the get_users method
        result = self.user.get_users()

        # Assert that the execute method was called with the correct query
        self.mock_cursor.execute.assert_called_once_with("SELECT * FROM user")

        # Assert that the result matches the mocked results
        self.assertEqual(
            result,
            '[{"column1": "value1", "column2": "value2"}, {"column1": "value1", "column2": "value2"}]',
        )


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
