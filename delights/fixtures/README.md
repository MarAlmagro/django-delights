# Fixtures

Development fixtures for Django Delights application.

## Available Fixtures

- `units.json` - Measurement units (gram, kilogram, liter, etc.)
- `ingredients.json` - Sample ingredients with prices and quantities
- `dishes.json` - Sample dishes with recipe requirements
- `menus.json` - Sample menus containing multiple dishes
- `users.json` - Sample admin and staff user accounts

## Loading Fixtures

To load all fixtures:

```bash
python manage.py loaddata units ingredients dishes menus users
```

To load specific fixtures:

```bash
python manage.py loaddata units
python manage.py loaddata ingredients
# etc.
```

## Creating Fixtures

To create fixtures from existing data:

```bash
python manage.py dumpdata delights.Unit --indent 2 > delights/fixtures/units.json
python manage.py dumpdata delights.Ingredient --indent 2 > delights/fixtures/ingredients.json
# etc.
```

## Note

Fixtures are for development and testing purposes only. Do not use in production.

