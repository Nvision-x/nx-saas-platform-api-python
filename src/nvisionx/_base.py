from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, ValidatorFunctionWrapHandler, WrapValidator


class NxModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


def _accept_unknown(value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
    try:
        return handler(value)
    except ValidationError:
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            return value
        raise


Open = WrapValidator(_accept_unknown)
