from uuid import UUID
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DatetimeMixin:
    created: datetime
    modified: datetime


@dataclass
class UUIDMixin:
    id: UUID

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)


@dataclass
class FilmWork(UUIDMixin, DatetimeMixin):
    title: str
    description: str
    creation_date: datetime.date
    rating: float
    type: str


@dataclass
class Genre(UUIDMixin, DatetimeMixin):
    name: str
    description: str


@dataclass
class Person(UUIDMixin, DatetimeMixin):
    full_name: str


@dataclass
class GenreFilmWork(UUIDMixin):
    genre_id: UUID
    film_work_id: UUID
    created: datetime

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)
        if isinstance(self.genre_id, str):
            self.genre_id = UUID(self.genre_id)
        if isinstance(self.film_work_id, str):
            self.film_work_id = UUID(self.film_work_id)


@dataclass
class PersonFilmWork(UUIDMixin):
    person_id: UUID
    film_work_id: UUID
    role: str
    created: datetime

    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = UUID(self.id)
        if isinstance(self.person_id, str):
            self.person_id = UUID(self.person_id)
        if isinstance(self.film_work_id, str):
            self.film_work_id = UUID(self.film_work_id)


table_fabric = {
    'film_work': FilmWork,
    'genre': Genre,
    'person': Person,
    'genre_film_work': GenreFilmWork,
    'person_film_work': PersonFilmWork
}


class DifferentColumn(Enum):
    created = 'created_at'
    modified = 'updated_at'
