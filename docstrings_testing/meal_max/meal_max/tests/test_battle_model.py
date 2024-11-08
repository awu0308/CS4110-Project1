import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal

@pytest.fisxture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

@pytest.fixture
def mock_get_random(mocker):
    """Mock the get random function for testing purposes."""
    return mocker.patch("meal_max.models.battle_model.py.BattleModel.get_random")

"""Fixtures providing sample combatants for the tests."""
@pytest.fixture
def sample_meal1():
    return Meal(1, 'meal 1', 'computer', 90000.00, 'HIGH')

@pytest.fixture
def sample_meal2():
    return Meal(2, 'meal 2', 'science', 2024.00, 'LOW')

@pytest.fixture
def sample_battle(sample_song1, sample_song2):
    return [sample_song1, sample_song2]

##################################################
# battle test cases
##################################################

##################################################
# clear_combatant test cases
##################################################

##################################################
# get_battle_score test cases
##################################################

##################################################
# get_combatants test cases
##################################################

##################################################
# prep_combatant test cases
##################################################