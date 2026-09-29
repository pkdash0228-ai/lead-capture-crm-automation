from pydantic import BaseModel, ConfigDict, EmailStr


class LeadInput(BaseModel):
    name: str
    email: EmailStr
    company: str
    message: str


class LeadUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    company: str | None = None
    message: str | None = None
    status: str | None = None


class Lead(LeadInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    status: str
    created_at: str
    updated_at: str
