from pydantic import BaseModel, constr


class URLBase(BaseModel):
    target_url: str
    custom: constr(strip_whitespace=True, min_length=4, max_length=10) | None = None


class URL(URLBase):
    is_active: bool
    clicks: int

    class Config:
        orm_mode = True


class URLInfo(URL):
    url: str
    admin_url: str
