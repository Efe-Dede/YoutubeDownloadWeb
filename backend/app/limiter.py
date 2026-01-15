"""Rate limiter configuration."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize Rate Limiter globally
# default_limits: Default limit for endpoints without specific decoration
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
