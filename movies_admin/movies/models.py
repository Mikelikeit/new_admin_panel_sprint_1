import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('name'), max_length=255, unique=True)
    description = models.TextField(_('description'), blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = _('genre')
        verbose_name_plural = _('genres')
        indexes = [
            models.Index(
                fields=['id', 'name'],
                name='genre_id_genre_name_idx',
            ),
        ]


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField(_('full_name'), max_length=255, unique=True)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = "content\".\"person"
        verbose_name = _('person')
        verbose_name_plural = _('persons')
        indexes = [
            models.Index(
                fields=['id', 'full_name'],
                name='person_id_person_full_name_idx',
            ),
        ]


class FilmWork(UUIDMixin, TimeStampedMixin):
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)
    creation_date = models.DateField(_('creation_date'), blank=True, null=True)
    rating = models.FloatField(_('rating'),
                               validators=[MinValueValidator(0.0),
                                           MaxValueValidator(100.0)], null=True)

    class Type(models.TextChoices):
        movie = 'movie', _('movie')
        tv_show = 'tv_show', _('tv_show')

    type = models.CharField(_('type'), max_length=255,
                            choices=Type.choices, default=Type.movie)
    genres = models.ManyToManyField(Genre, through='GenreFilmWork')
    persons = models.ManyToManyField(Person, through='PersonFilmWork')

    def __str__(self):
        return self.title

    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = _('film_work')
        verbose_name_plural = _('film_works')
        indexes = [
            models.Index(
                fields=['id', 'creation_date'],
                name='film_work_id_creation_date_idx',
            ),
        ]


class GenreFilmWork(UUIDMixin):
    film_work = models.ForeignKey(FilmWork, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE,
                              verbose_name=_('genre'))
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"genre_film_work"
        verbose_name = _('genre_film_work')
        verbose_name_plural = _('genres_film_works')
        indexes = [
            models.Index(
                fields=['id', 'genre_id'],
                name='gfw_id_genre_id_idx',
            ),
            models.Index(
                fields=['id', 'film_work_id'],
                name='gfw_id_film_work_id_idx',
            ),
        ]


class PersonFilmWork(UUIDMixin):
    film_work = models.ForeignKey(FilmWork, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
                               verbose_name=_('person'))

    class Role(models.TextChoices):
        actor = 'actor', _('actor')
        writer = 'writer', _('writer')
        director = 'director', _('director')
    role = models.CharField(_('role'), max_length=255, choices=Role.choices)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"person_film_work"
        verbose_name = _('person_film_work')
        verbose_name_plural = _('persons_film_works')
        indexes = [
            models.Index(
                fields=['id', 'person_id'],
                name='pfw_id_person_id_idx',
            ),
            models.Index(
                fields=['id', 'film_work_id'],
                name='pfw_id_film_work_id_idx',
            ),
        ]
