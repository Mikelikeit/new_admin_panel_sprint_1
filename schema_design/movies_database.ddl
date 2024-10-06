CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE IF NOT EXISTS content.film_work (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    creation_date DATE,
    rating FLOAT,
    type VARCHAR(255) NOT NULL,
    created TIMESTAMP WITH TIME ZONE,
    modified TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS content.genre (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created TIMESTAMP WITH TIME ZONE,
    modified TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS content.person (
    id UUID PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL UNIQUE,
    created TIMESTAMP WITH TIME ZONE,
    modified TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS content.genre_film_work (
    id UUID PRIMARY KEY,
    genre_id UUID NOT NULL,
    film_work_id UUID NOT NULL,
    created TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_genre_id
        FOREIGN KEY (genre_id)
        REFERENCES content.genre (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_film_work_id
        FOREIGN KEY (film_work_id)
        REFERENCES content.film_work (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS content.person_film_work (
    id UUID PRIMARY KEY,
    person_id UUID NOT NULL,
    film_work_id UUID NOT NULL,
    role VARCHAR(255) NOT NULL,
    created TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_person_id
        FOREIGN KEY (person_id)
        REFERENCES content.person (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_film_work_id
        FOREIGN KEY (film_work_id)
        REFERENCES content.film_work (id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS film_work_id_film_work_creation_date_idx ON content.film_work (id, creation_date);

CREATE INDEX IF NOT EXISTS genre_id_genre_name_idx ON content.genre (id, name);

CREATE INDEX IF NOT EXISTS person_id_person_full_name_idx ON content.person (id, full_name);

CREATE INDEX IF NOT EXISTS gfw_id_genre_id_idx ON content.genre_film_work (id, genre_id);
CREATE INDEX IF NOT EXISTS gfw_id_film_work_id_idx ON content.genre_film_work (id, film_work_id);
CREATE UNIQUE INDEX IF NOT EXISTS film_work_genre_idx ON content.person_film_work (film_work_id, genre_id);

CREATE INDEX IF NOT EXISTS pfw_id_person_id_idx ON content.person_film_work (id, person_id);
CREATE INDEX IF NOT EXISTS pfw_id_film_work_id_idx ON content.person_film_work (id, film_work_id);
CREATE UNIQUE INDEX IF NOT EXISTS film_work_person_idx ON content.person_film_work (film_work_id, person_id);