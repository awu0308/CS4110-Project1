import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal

@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

@pytest.fixture
def mock_get_random(mocker):
    """Mock the get random function for testing purposes."""
    return mocker.patch("meal_max.models.battle_model.BattleModel.get_random")

"""Fixtures providing sample combatants for the tests."""
@pytest.fixture
def sample_meal1():
    return Meal(1, 'Meal 1', 'computer', 9000.00, 'HIGH')

@pytest.fixture
def sample_meal2():
    return Meal(2, 'Meal 2', 'science', 2024.00, 'LOW')

@pytest.fixture
def sample_meal3():
    return Meal(3, 'Meal 3', 'art', 300.00, 'MED')

@pytest.fixture
def sample_battle(sample_meal1, sample_meal2):
    return [sample_meal1, sample_meal2]

##################################################
# battle test cases
##################################################
def test_battle_meal1_wins(battle_model, sample_meal1, sample_meal2, mock_get_random):
    """
    Test that the battle method returns sample_meal1 as the winner.
    """
    # (((9000*8-1) - (2024*7-3))/100) > 0.3
    mock_get_random.return_value = 0.3  

    winner = battle_model.battle(sample_meal1, sample_meal2)

    assert winner == sample_meal1, f"Expected winner {sample_meal1.meal}, but got {winner.meal}"

def test_battle_meal2_wins(battle_model, sample_meal1, sample_meal2, mock_get_random):
    """
    Test that the battle method returns sample_meal2 as the winner.
    """
    # (((9000*8-1) - (2024*7-3))/100) < 9000
    mock_get_random.return_value = 9000 

    winner = battle_model.battle(sample_meal1, sample_meal2)

    # Assert
    assert winner == sample_meal2, f"Expected winner {sample_meal2.meal}, but got {winner.meal}"


##################################################
# clear_combatant test cases
##################################################
def test_clear_combatant(battle_model, sample_meal1, sample_meal2):
    """
    Test that the clear_combatant method removes the specified combatant.
    
    """
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    # Use clear_combatant to remobe sample_model1
    battle_model.clear_combatants()

    # Check if only sample_meal2 remains
    assert sample_meal1 not in battle_model.combatants
    assert sample_meal2 in battle_model.combatants
    assert len(battle_model.combatants) == 1

##################################################
# get_battle_score test cases
##################################################
def test_get_battle_score_high(battle_model, sample_meal1):
    """
    Test getting the battle score of a combatant with HIGH difficulty.
    """
    score = battle_model.get_battle_score(sample_meal1)
    expected_score = (sample_meal1.price * len(sample_meal1.cuisine)) - 1  # 1 is the modifier for "HIGH"
    assert score == expected_score, f"Expected {expected_score}, but got {score}"

def test_get_battle_score_low(battle_model, sample_meal2):
    """
    Test getting the battle score of a combatant with LOW difficulty.
    """
    score = battle_model.get_battle_score(sample_meal2)
    expected_score = (sample_meal2.price * len(sample_meal2.cuisine)) - 3  # 3 is the modifier for "LOW"
    assert score == expected_score, f"Expected {expected_score}, but got {score}"

def test_get_battle_score_med(battle_model, sample_meal3):
    """
    Test getting the battle score of a combatant with MED difficulty.
    """
    score = battle_model.get_battle_score(sample_meal3)
    expected_score = (sample_meal3.price * len(sample_meal3.cuisine)) - 2  # 2 is the modifier for "MED"
    assert score == expected_score, f"Expected {expected_score}, but got {score}"
##################################################
# get_combatants test cases
##################################################
def test_get_combatants(battle_model, sample_battle):
    """
    Test getting the combatants.
    
    """
    battle_model.combatants.extend(sample_battle)

    all_combatants = battle_model.get_combatants()
    assert len(all_combatants)
    assert all_combatants[0].meal

##################################################
# prep_combatant test cases
##################################################
def test_prep_combatant(battle_model, sample_meal1):
    """
    Test adding a Meal to the battle as a combatant.
    
    """
    battle_model.prep_combatant(sample_meal1)

    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == 'Meal 1'

def test_more_than_2_prep_combatant(battle_model, sample_meal1, sample_meal2, sample_meal3):
    """
    Test adding more than 2 Meals to the battle.
    
    """
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(sample_meal3)