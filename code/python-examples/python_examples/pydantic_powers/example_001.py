import uuid
from pydantic import BaseModel


class RawSentence(BaseModel):
    id: uuid.UUID  # An id has to match a UUID
    text: str  # The text has to match a normal str


if __name__ == "__main__":
    data_point = {
        "id": "4a3f61a9-8e75-4341-b3a0-3e64e0b60fb6",
        "text": "Hello I'm a raw sentence",
    }
    model = RawSentence(**data_point)
    print(model)
    # id=UUID('4a3f61a9-8e75-4341-b3a0-3e64e0b60fb6') text='Hello Im a raw sentence'
    print(model.id)
    # 4a3f61a9-8e75-4341-b3a0-3e64e0b60fb6

    model = RawSentence(**{"id": "", "text": "Hello Im a raw sentence"})
    # model = RawSentence(**{"id": "", "text": 15})
    #   File "pydantic/main.py", line 406, in pydantic.main.BaseModel.__init__
    # pydantic.error_wrappers.ValidationError: 1 validation error for RawSentence
    # id
    #   value is not a valid uuid (type=type_error.uuid)
''