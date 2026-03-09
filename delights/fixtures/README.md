# Fixtures

Development fixtures for the Django Delights application.

This directory is set up to hold sample data in JSON format. **No fixture files are included in the repository by default** — you can generate them from your own data.

## Creating Fixtures

To export your current data as fixtures:

```bash
python manage.py dumpdata delights.Unit --indent 2 > delights/fixtures/units.json
python manage.py dumpdata delights.Ingredient --indent 2 > delights/fixtures/ingredients.json
python manage.py dumpdata delights.Dish delights.RecipeRequirement --indent 2 > delights/fixtures/dishes.json
python manage.py dumpdata delights.Menu --indent 2 > delights/fixtures/menus.json
python manage.py dumpdata auth.User --indent 2 > delights/fixtures/users.json
```

## Loading Fixtures

Order matters due to foreign key dependencies:

```bash
# Load all (recommended order)
python manage.py loaddata units ingredients dishes menus users

# Load individually
python manage.py loaddata units
python manage.py loaddata ingredients
```

## Note

Fixtures are for development and testing purposes only. Do not use in production.

