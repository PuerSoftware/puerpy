from pydantic import BaseModel

class Event(BaseModel):
    name: str
    data: dict | str
    meta: dict = {}
