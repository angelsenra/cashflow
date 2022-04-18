import logging
import secrets
import uuid

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def generate_unsecure_public_id():
    # https://en.wikipedia.org/wiki/Birthday_attack#Simple_approximation
    # n=2**24; p=2**(-25); H=n**2/2*p = 2**48/2**(-24) = 2**72; b=log2(H)/8 = 9
    # I.e. after generating 16 million rows in the same table, the chances of a collision are still 1 in 33 million.
    # So we MUST NOT use this for secrets or "unguessable" URLs. But it's safe to use them when for URLs where we are
    # also checking the user access. So if someone got their hands on this id, they still would need access to it.

    return secrets.token_urlsafe(9)


def generate_order():
    return int(timezone.now().timestamp())


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(unique=True, default=generate_unsecure_public_id, max_length=50, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"<{self.__class__.__name__} {self.public_id}>"
