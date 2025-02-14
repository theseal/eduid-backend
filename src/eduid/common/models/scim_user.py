from typing import Any, Dict, List, Optional

from pydantic import Field

from eduid.common.models.scim_base import (
    BaseCreateRequest,
    BaseResponse,
    BaseUpdateRequest,
    EduidBaseModel,
    Email,
    LanguageTag,
    Name,
    PhoneNumber,
    SCIMSchema,
    SubResource,
)

__author__ = "lundberg"


class Profile(EduidBaseModel):
    attributes: Dict[str, Any] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.dict()


class LinkedAccount(EduidBaseModel):
    issuer: str
    value: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.dict()


class NutidUserExtensionV1(EduidBaseModel):
    profiles: Dict[str, Profile] = Field(default_factory=dict)
    linked_accounts: List[LinkedAccount] = Field(default_factory=list)


class Group(SubResource):
    pass


class User(EduidBaseModel):
    name: Name = Field(default_factory=Name)
    emails: List[Email] = Field(default_factory=list)
    phone_numbers: List[PhoneNumber] = Field(default_factory=list, alias="phoneNumbers")
    preferred_language: Optional[LanguageTag] = Field(default=None, alias="preferredLanguage")
    groups: List[Group] = Field(default_factory=list)
    nutid_user_v1: Optional[NutidUserExtensionV1] = Field(
        default_factory=NutidUserExtensionV1, alias=SCIMSchema.NUTID_USER_V1.value
    )


class UserCreateRequest(User, BaseCreateRequest):
    pass


class UserUpdateRequest(User, BaseUpdateRequest):
    pass


class UserResponse(User, BaseResponse):
    pass
