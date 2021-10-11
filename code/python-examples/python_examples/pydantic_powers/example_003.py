import typing
from pydantic import BaseModel


class Related(BaseModel):
    name: str


class Product(BaseModel):
    price: typing.Union[int, float]
    flag: typing.Optional[str]
    tags: typing.List[str]
    related: typing.Optional[typing.Dict]
    model: typing.Literal["A", "B", "C", "D"]
    related_model: Related


if __name__ == "__main__":
    product = Product(
        **{
            "price": 1,
            "tags": ["awesome"],
            "model": "A",
            "related_model": {"name": "ChildName"},
        }
    )
    print(product)
    # price=1 flag=None tags=['awesome'] related=None model='A' related_model=Related(name='ChildName')
    print(product.related_model)
    # name='ChildName'
