CREATE TABLE positions (
    position_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE subpositions (
    subposition_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    position_id INT NOT NULL,
    FOREIGN KEY (position_id) REFERENCES positions(position_id)
);

CREATE TABLE countries (
    country_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    continent VARCHAR(100)
);

CREATE TABLE competitions (
    competition_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    country_id INT,
    is_major_league BOOLEAN DEFAULT FALSE,
    url TEXT,
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

CREATE TABLE clubs (
    club_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    domestic_comp_id INT,
    stadium_name VARCHAR(150),
    stadium_capacity INT,
    squad_size INT,
    average_age DECIMAL(4,2),
    foreign_number INT,
    national_number INT,
    FOREIGN KEY (domestic_comp_id) REFERENCES competitions(competition_id)
);

CREATE TABLE players (
    player_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    birthdate DATE,
    subposition_id INT,
    height INT,
    foot VARCHAR(10),
    current_club_id INT,
    FOREIGN KEY (subposition_id) REFERENCES subpositions(subposition_id),
    FOREIGN KEY (current_club_id) REFERENCES clubs(club_id)
);

CREATE TABLE games (
    game_id INT AUTO_INCREMENT PRIMARY KEY,
    home_club_id INT,
    away_club_id INT,
    competition_id INT,
    home_goals INT,
    away_goals INT,
    game_date DATE,
    home_club_pos INT,
    away_club_pos INT,
    season VARCHAR(20),
    FOREIGN KEY (home_club_id) REFERENCES clubs(club_id),
    FOREIGN KEY (away_club_id) REFERENCES clubs(club_id),
    FOREIGN KEY (competition_id) REFERENCES competitions(competition_id)
);

CREATE TABLE transfers (
    transfer_id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT,
    from_club_id INT,
    to_club_id INT,
    transfer_date DATE,
    season VARCHAR(20),
    fee DECIMAL(15,2),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (from_club_id) REFERENCES clubs(club_id),
    FOREIGN KEY (to_club_id) REFERENCES clubs(club_id)
);