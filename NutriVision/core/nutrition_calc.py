def calculate_nutrition(recipe_dict, grams):
    """Scale macros by grams/100."""
    factor = grams / 100.0
    return {
        'calories': recipe_dict.get('calories', 0) * factor,
        'protein': recipe_dict.get('protein', 0) * factor,
        'fat': recipe_dict.get('fat', 0) * factor,
        'carbs': recipe_dict.get('carbs', 0) * factor,
    }


def get_daily_totals(logs_list):
    """Sum all macros from a list of log dicts (each must have calories, protein, fat, carbs scaled)."""
    totals = {'calories': 0.0, 'protein': 0.0, 'fat': 0.0, 'carbs': 0.0}
    for log in logs_list:
        factor = log.get('actual_intake_grams', 100) / 100.0
        totals['calories'] += log.get('calories', 0) * factor
        totals['protein'] += log.get('protein', 0) * factor
        totals['fat'] += log.get('fat', 0) * factor
        totals['carbs'] += log.get('carbs', 0) * factor
    return totals


def completion_score(logs_list, targets):
    """Return 0.0–1.0 based on calorie target met."""
    if not targets or targets.get('calories', 0) == 0:
        return 0.0
    totals = get_daily_totals(logs_list)
    score = totals['calories'] / targets['calories']
    return min(score, 1.0)
