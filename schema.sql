CREATE TABLE positions (
    position_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE subpositions (
    subposition_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    position_id INT NOT NULL REFERENCES positions(position_id)
);

CREATE TABLE countries (
    country_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    continent VARCHAR(100)
);

CREATE TABLE competitions (
    competition_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    country_id INT REFERENCES countries(country_id),
    is_major_league BOOLEAN DEFAULT FALSE,
    url TEXT
);

CREATE TABLE clubs (
    club_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    domestic_comp_id INT REFERENCES competitions(competition_id),
    stadium_name VARCHAR(150),
    stadium_capacity INT,
    squad_size INT,
    average_age DECIMAL(4,2),
    foreign_number INT,
    national_number INT
);

CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    birthdate DATE,
    subposition_id INT REFERENCES subpositions(subposition_id),
    height INT,
    foot VARCHAR(10),
    current_club_id INT REFERENCES clubs(club_id)
);

CREATE TABLE games (
    game_id SERIAL PRIMARY KEY,
    home_club_id INT REFERENCES clubs(club_id),
    away_club_id INT REFERENCES clubs(club_id),
    competition_id TEXT,
    home_club_goals INT,
    away_club_goals INT,
    date DATE,
    home_club_position INT,
    away_club_position INT,
    season VARCHAR(20)
);

CREATE TABLE transfers (
    transfer_id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(player_id),
    from_club_id INT REFERENCES clubs(club_id),
    to_club_id INT REFERENCES clubs(club_id),
    transfer_date DATE,
    season VARCHAR(20),
    fee DECIMAL(15,2)
);
