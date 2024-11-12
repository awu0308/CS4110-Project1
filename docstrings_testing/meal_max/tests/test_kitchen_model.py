from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats,
)

######################################################
#
#    Fixtures
#
######################################################
def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch('meal_max.models.kitchen_model.get_db_connection', mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal in the catalog."""

    # Call the function to create a new meal
    create_meal("Meal Name", "Meal Cuisine", 10.0, "HIGH")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Meal Name", "Meal Cuisine", 10.0, "HIGH")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}." 


def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate meal name (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with name 'Meal Name' already exists"):
        create_meal(meal="Meal Name", cuisine="Cuisine", price=10.0, difficulty="HIGH")

def test_create_meal_invalid_difficulty():
    """Test error when trying to create a meal with an invalid difficulty (e.g., not HIGH, MED, or LOW)."""

    # Attempt to create a meal with a difficulty that is not HIGH, MED, or LOW  
    with pytest.raises(ValueError, match="Invalid difficulty level: EASY. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Meal Name", cuisine="Cuisine", price=10.0, difficulty='EASY')

    # Attempt to create a meal with a lower case difficulty
    with pytest.raises(ValueError, match="Invalid difficulty level: high. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Meal Name", cuisine="Cuisine", price=10.0, difficulty='high')

def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an negative number."""

    # Attempt to create a meal with a price that is not positive  
    with pytest.raises(ValueError, match="Invalid price: -180.0. Price must be a positive number."):
        create_meal(meal="Meal Name", cuisine="Cuisine", price=-180.0, difficulty='-HIGH')
    
    # Attempt to create a meal with a price that is not a number  
    with pytest.raises(ValueError, match="Invalid price: one. Price must be a positive number."):
        create_meal(meal="Meal Name", cuisine="Cuisine", price="one", difficulty='HIGH')


def test_delete_meal(mock_cursor):
    """Test soft deleting a meal from the catalog by meal ID."""

    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = ([False])

    # Call the delete_meal function
    delete_meal(1)

    # Normalize the SQL for both queries (SELECT and UPDATE)
    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Ensure the correct SQL queries were executed
    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."


def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when attempting to delete a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""

    # Simulate that the meal exists but is already marked as deleted
    mock_cursor.fetchone.return_value = ([True])

    # Expect a ValueError when attempting to delete a song that's already been deleted
    with pytest.raises(ValueError, match="Meal with ID 999 has been deleted"):
        delete_meal(999)

def test_clear_catalog(mock_cursor, mocker):
    """Test clearing the entire meal database (removes all meals)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_song_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_database function
    clear_meals()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_song_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once()

######################################################
#
#    Get Leaderboard
#
######################################################

def test_get_leaderboard_wins(mock_cursor):
    """Test retrieving all meals ordered by win count."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (2, "Meal B", "Cuisine B", 30.0, 'HIGH', 30, 15, 0.5),
        (1, "Meal A", "Cuisine A", 20.0, 'MED', 10, 10, 1.0),
        (3, "Meal C", "Cuisine C", 10.0, 'LOW', 20, 5, 0.20)
    ]

    # Call the get_leaderboard function with sort_by = "wins"
    meals = get_leaderboard(sort_by="wins")

    # Ensure the results are sorted by wins
    expected_result = [
        {"id": 2, "meal": "Meal B", "cuisine": "Cuisine B", "price": 30.0, "difficulty": 'HIGH', "battles": 30, "wins": 15, "win_pct": 50.0},
        {"id": 1, "meal": "Meal A", "cuisine": "Cuisine A", "price": 20.0, "difficulty": 'MED', "battles": 10, "wins": 10, "win_pct": 100.0},
        {"id": 3, "meal": "Meal C", "cuisine": "Cuisine C", "price": 10.0, "difficulty": 'LOW', "battles": 20, "wins": 5, "win_pct": 20.0}
    ]

    assert meals == expected_result, f"Expected {expected_result}, but got {meals}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_win_pct(mock_cursor):
    """Test retrieving all meals ordered by win percentage."""

    # Simulate that there are multiple meals in the database
    mock_cursor.fetchall.return_value = [
        (1, "Meal A", "Cuisine A", 20.0, 'MED', 10, 10, 1.0),
        (2, "Meal B", "Cuisine B", 30.0, 'HIGH', 30, 15, 0.5),
        (3, "Meal C", "Cuisine C", 10.0, 'LOW', 20, 5, 0.20)
    ]

    # Call the get_leaderboards function with sort_by = "win_pct"
    meals = get_leaderboard(sort_by="win_pct")

    # Ensure the results are sorted by win percentage
    expected_result = [
        {"id": 1, "meal": "Meal A", "cuisine": "Cuisine A", "price": 20.0, "difficulty": 'MED', "battles": 10, "wins": 10, "win_pct": 100.0},
        {"id": 2, "meal": "Meal B", "cuisine": "Cuisine B", "price": 30.0, "difficulty": 'HIGH', "battles": 30, "wins": 15, "win_pct": 50.0},
        {"id": 3, "meal": "Meal C", "cuisine": "Cuisine C", "price": 10.0, "difficulty": 'LOW', "battles": 20, "wins": 5, "win_pct": 20.0}
    ]

    assert meals == expected_result, f"Expected {expected_result}, but got {meals}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY win_pct DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_invalid_sort_by(mock_cursor):
    """Test error when trying to sort the leaderboard by an invalid metric."""

    # Expect a ValueError when an invalid sort_by parameter is provided
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid"):
        get_leaderboard(sort_by="invalid")


######################################################
#
#    get_meal
#
######################################################

def test_get_meal_by_id(mock_cursor):
    """Test retrieving a meal from the catalog by meal ID."""
    # Simulate that the meal exists (id = 1)
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine", 10, 'HIGH', False)

    # Call the function and check the result
    result = get_meal_by_id(1)

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine", 10, 'HIGH')

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = (1,)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_id_bad_id(mock_cursor):
    """Test error when trying to retrieve a meal that does not exist."""
    # Simulate that no meal exists for the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the song is not found
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_id_deleted_meal(mock_cursor):
    """Test error when trying to retrieve a deleted meal from the catalog."""
    # Simulate that the meal exists but is marked as deleted
    mock_cursor.fetchone.return_value = mock_cursor.fetchone.return_value = (1, 'Meal Name', 'Cuisine Type', 50.0, 'Medium', True)

    # Expect a ValueError when trying to retrieve a deleted meal
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)

def test_get_meal_by_name(mock_cursor):
    """Test retrieving a meal from the catalog by meal name."""
    # Simulate that the meal exists (meal = "Meal Name", cuisine = "Cuisine", price = 10, difficulty = 'HIGH')
    mock_cursor.fetchone.return_value = (1, "Meal Name", "Cuisine", 10, 'HIGH', False)

    # Call the function and check the result
    result = get_meal_by_name("Meal Name")

    # Expected result based on the simulated fetchone return value
    expected_result = Meal(1, "Meal Name", "Cuisine", 10, 'HIGH')

    # Ensure the result matches the expected output
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ('Meal Name',)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_meal_by_bad_name(mock_cursor):
    """Test error when trying to retrieve a meal that does not exist."""
    # Simulate that no meal exists for the given name
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when the meal is not found
    with pytest.raises(ValueError, match="Meal with name Meal D not found"):
        get_meal_by_name("Meal D")

def test_get_meal_by_deleted_meal(mock_cursor):
    """Test error when trying to retrieve a deleted meal from the catalog."""
    # Simulate that the meal exists but is marked as deleted
    mock_cursor.fetchone.return_value = (1, 'Meal Name', 'Cuisine Type', 50.0, 'Medium', True)

    # Expect a ValueError when trying to retrieve a deleted meal
    with pytest.raises(ValueError, match="Meal with name Meal Name has been deleted"):
        get_meal_by_name("Meal Name")


######################################################
#
#    update_meal
#
######################################################
def test_update_meal_stats_win(mock_cursor):
    """Test updating the stats of a meal given it won."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_play_count function with a sample meal ID and result
    meal_id = 1
    result = "win"
    update_meal_stats(meal_id, result)

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id, )
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_loss(mock_cursor):
    """Test updating the stats of a meal given it lost."""

    # Simulate that the meal exists and is not deleted (id = 1)
    mock_cursor.fetchone.return_value = [False]

    # Call the update_play_count function with a sample meal ID and result
    meal_id = 1
    result = "loss"
    update_meal_stats(meal_id, result)

    # Normalize the expected SQL query
    expected_query = normalize_whitespace("""
        UPDATE meals SET battles = battles + 1 WHERE id = ?
    """)

    # Ensure the SQL query was executed correctly
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]

    # Assert that the SQL query was executed with the correct arguments (meal ID)
    expected_arguments = (meal_id, )
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_update_meal_stats_deleted_meal(mock_cursor):
    """Test error when trying to update the stats of a deleted meal."""

    # Simulate that the meal exists but is marked as deleted
    mock_cursor.fetchone.return_value = [True]

    # Expect a ValueError when trying to update the stats of a deleted meal
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "win")
    
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))

def test_update_meal_stats_bad_id(mock_cursor):
    """Test error when trying to update the stats of a non-existent meal."""

    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    # Expect a ValueError when trying to update the stats of a non-existent meal
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        update_meal_stats(999, "win")
    
    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (999,))

def test_update_meal_stats_invalid_result(mock_cursor):
    """Test error when trying to update the stats of a meal with an invalid result."""

    mock_cursor.fetchone.return_value = [False]

    # Expect a ValueError when an invalid result parameter is provided
    with pytest.raises(ValueError, match="Invalid result: invalid. Expected 'win' or 'loss'."):
        update_meal_stats(1, "invalid")

    mock_cursor.execute.assert_called_once_with("SELECT deleted FROM meals WHERE id = ?", (1,))