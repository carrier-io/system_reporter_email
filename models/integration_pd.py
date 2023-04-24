import binascii
import smtplib
from typing import Optional, List, Union

from pydantic import BaseModel, EmailStr
from pydantic.class_validators import validator
from pydantic.fields import ModelField
from pylon.core.tools import log

import base64

from ...integrations.models.pd.integration import SecretField


class IntegrationModel(BaseModel):

    # TODO: Update template
    _default_template = 'PGRpdj5EZWZhdWx0IHRlbXBsYXRlPC9kaXY+'

    host: str
    port: int
    user: str
    passwd: Union[SecretField, str]
    sender: Optional[str]
    template: Optional[str] = _default_template

    def check_connection(self, **kwargs) -> bool:
        try:
            with smtplib.SMTP_SSL(host=self.host, port=self.port) as server:
                server.ehlo()
                server.login(self.user, self.passwd.unsecret(kwargs.get('project_id')))
            return True
        except Exception as e:
            log.exception(e)
            return False

    @validator('template')
    def validate_base64(cls, value: str, field: ModelField):
        if value:
            try:
                base64.b64decode(value, validate=True)
            except binascii.Error:
                log.error('Email template must be base64-encoded')
                raise
            return value
        else:
            return field.default


class TaskSettingsModel(IntegrationModel):
    galloper_url: str = '{{secret.galloper_url}}'
    token: str = '{{secret.auth_token}}'
    project_id: Optional[int]
    passwd: str

    @validator('passwd', pre=True)
    def unsecret_passwd(cls, value, values: dict):
        if isinstance(value, SecretField):
            return value.unsecret(project_id=values['project_id'])
        elif isinstance(value, dict):
            return SecretField.parse_obj(value).unsecret(project_id=values.get('project_id'))
        return value
