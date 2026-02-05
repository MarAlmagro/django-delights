# Settings package
# Import the appropriate settings based on environment

import os

environment = os.getenv("DJANGO_ENV", "dev")

if environment == "prod":
    from .prod import *  # noqa: F401, F403
else:
    from .dev import *  # noqa: F401, F403
