import uuid
from pydantic import BaseModel


def to_camel(string: str) -> str:
    return "".join(word.capitalize() for word in string.split("_"))


class Scheme(BaseModel):
    class Config:
        alias_generator = to_camel


class ResponseScheme(Scheme):
    user_id: uuid.UUID
    document_id: uuid.UUID


if __name__ == "__main__":
    response_scheme = ResponseScheme(
        **{"UserId": uuid.uuid4(), "DocumentId": uuid.uuid4(),}
    )
    print(response_scheme.json())
    # {"user_id": "489bee33-7f7e-4b09-b83b-2d44ebeffde6", "document_id": "5e47e30d-d175-457d-8737-84cd06eae3f0"}
