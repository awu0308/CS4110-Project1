#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

# Health checks
check_health
check_db

# meal management
clear_catalog() {
  echo "Clearing all meals..."
  curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'

}

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  json_data="{\"meal\":\"$meal\", \"price\":$price, \"cuisine\":\"$cuisine\", \"difficulty\":\"$difficulty\"}"
  echo "JSON Data: $json_data"  # This will print the JSON for debugging
  echo "Adding meal ($meal) with price $price, cuisine $cuisine, difficulty $difficulty..."
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"price\":$price, \"cuisine\":\"$cuisine\", \"difficulty\":\"$difficulty\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal_by_id() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
  else
    echo "Failed to delete meal by ID ($meal_id)."
    exit 1
  fi
}


get_meal_by_id() {
  meal_id=$1

  echo "Getting meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by ID ($meal_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by ID ($meal_id)."
    exit 1
  fi
}

# Function to get leaderboard
get_leaderboard() {
    sort_by=${1:-"wins"}  # Default to "wins" if no parameter is provided
    echo "Retrieving leaderboards by ($sort_by)"
    response=$(curl -s -X GET "$BASE_URL/leaderboard?sort_by=$(echo $sort_by | sed 's/ /%20/g')")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Leaderboard retrieved successfully by ($sort_by)"
        if [ "$ECHO_JSON" = true ]; then
            echo "Leaderboard JSON:"
            echo "$response" | jq .
        fi
    else
        echo "Failed to retrieve leaderboard."
        echo "$response"
    fi
}


# Function to get a meal by name
get_meal_by_name() {
  meal_name=$1

  echo "Getting meal by name ($meal_name)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name/$meal_name")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name ($meal_name)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (Name: $meal_name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name ($meal_name)."
    exit 1
  fi
}

# Function to update meal stats
update_meal_stats() {
  meal_id=$1
  stat_type=$2  # e.g., "win" or "loss"

  echo "Updating stats for meal ID ($meal_id) with stat type ($stat_type)..."
  response=$(curl -s -X POST "$BASE_URL/update-meal-stats" -H "Content-Type: application/json" \
    -d "{\"meal_id\": $meal_id, \"stat_type\": \"$stat_type\"}")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal stats updated successfully for meal ID ($meal_id)."
  else
    echo "Failed to update meal stats for meal ID ($meal_id)."
    exit 1
  fi
}


# battle_model tests
prep_combatant() {
    local meal=$1
    echo "Preparing combatant ($meal)..."
    response=$(curl -s -X POST "$BASE_URL/prep-combatant" -H "Content-Type: application/json" \
        -d "{\"meal\": \"$meal\"}")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Combatant prepped successfully."
    else
        echo "Failed to prep combatant."
        echo "$response"
    fi
}

get_combatants() {
    echo "Retrieving combatants..."
    response=$(curl -s -X GET "$BASE_URL/get-combatants")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Combatants retrieved successfully."
        if [ "$ECHO_JSON" = true ]; then
            echo "Combatants JSON:"
            echo "$response" | jq .
        fi
    else
        echo "Failed to retrieve combatants."
        echo "$response"
    fi
}

battle() {
    echo "Starting battle..."
    response=$(curl -s -X GET "$BASE_URL/battle")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Battle completed successfully."
        if [ "$ECHO_JSON" = true ]; then
            echo "Battle result:"
            echo "$response" | jq .
        fi
    else
        echo "Failed to start battle."
        echo "$response"
    fi
}

clear_combatants() {
    echo "Clearing combatants..."
    response=$(curl -s -X POST "$BASE_URL/clear-combatants")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Combatants cleared successfully."
    else
        echo "Failed to clear combatants."
        echo "$response"
    fi
}

get_battle_score() {
    local meal_name=$1
    local price=$2
    local cuisine=$3
    local difficulty=$4

    echo "Getting battle score for ($meal_name)..."
    response=$(curl -s -X POST "$BASE_URL/get-battle-score" -H "Content-Type: application/json" \
        -d "{\"meal\": \"$meal_name\", \"price\": $price, \"cuisine\": \"$cuisine\", \"difficulty\": \"$difficulty\"}")
    if echo "$response" | grep -q '"status": "success"'; then
        echo "Battle score retrieved successfully."
        if [ "$ECHO_JSON" = true ]; then
            echo "Battle score JSON:"
            echo "$response" | jq .
        fi
    else
        echo "Failed to get battle score."
        echo "$response"
    fi
}

# Health checks
check_health
check_db

# Example usage of each function

create_meal "school lunch" "US" 2.49 "LOW"
clear_catalog
create_meal "pizza" "italian" 14.00 "MED"
get_meal_by_id 1
delete_meal_by_id 1

create_meal "whiskey" "alcohol" 90.00 "HIGH"
get_meal_by_name "whiskey"
get_leaderboard sort_by="win_pct"
# update_meal_stats 1 "win"
create_meal "Spaghetti" "Italian" 15.99 "MED"
prep_combatant "Spaghetti"
prep_combatant "whiskey"
get_combatants
battle
get_combatants
clear_combatants

create_meal "Hamburger" "American" 10.59 "MED"
prep_combatant "Spaghetti"
prep_combatant "whiskey"
get_combatants
battle
prep_combatant "Hamburger"
get_combatants
battle

get_meal_by_id 2
get_meal_by_id 3

get_leaderboard 
# get_battle_score "Burger" 10.50 "American" "LOW"
