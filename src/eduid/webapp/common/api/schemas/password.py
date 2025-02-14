# -*- coding: utf-8 -*-
from typing import List, Optional

from marshmallow import Schema, ValidationError

__author__ = "lundberg"

from eduid.webapp.common.api.validation import is_valid_password


class PasswordSchema(Schema):
    class Meta:
        zxcvbn_terms: Optional[List[str]] = None
        min_entropy: Optional[int] = None
        min_score: Optional[int] = None

    def __init__(self, *args, **kwargs):
        self.Meta.zxcvbn_terms = kwargs.pop("zxcvbn_terms", [])
        self.Meta.min_entropy = kwargs.pop("min_entropy")
        self.Meta.min_score = kwargs.pop("min_score")
        super(PasswordSchema, self).__init__(*args, **kwargs)

    def validate_password(self, password: str, **kwargs):
        """
        :param password: New password

        Checks the complexity of the password
        """
        if self.Meta.zxcvbn_terms is None or self.Meta.min_entropy is None or self.Meta.min_score is None:
            raise ValidationError("The password complexity cannot be determined.")
        try:
            if not is_valid_password(
                password=password,
                user_info=self.Meta.zxcvbn_terms,
                min_entropy=self.Meta.min_entropy,
                min_score=self.Meta.min_score,
            ):
                raise ValidationError("The password complexity is too weak.")
        except ValueError:
            raise ValidationError("The password complexity is too weak.")
