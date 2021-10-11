import typing
import uuid
from pydantic import BaseModel


class RawSentence(BaseModel):
    id: uuid.UUID  # An id has to match a UUID
    text: str  # The text has to match a normal str

    def filter_text_by_token_length(self, min_lenth: int) -> typing.List[str]:
        return [
            token
            for token in self.text.split()
            if len(token) >= min_lenth
        ]


if __name__ == "__main__":
    data_point = {
        "id": "4a3f61a9-8e75-4341-b3a0-3e64e0b60fb6",
        "text": "Hello I'm a raw sentence",
    }
    model = RawSentence(**data_point)
    filterd_tokens = model.filter_text_by_token_length(min_lenth=2)
    print(filterd_tokens)
    # ['Hello', "I'm", 'raw', 'sentence']
