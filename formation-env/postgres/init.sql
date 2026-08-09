CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

INSERT INTO clients (nom, email) VALUES
    ('Alice Martin', 'alice.martin@example.com'),
    ('Bruno Dupont', 'bruno.dupont@example.com'),
    ('Chloé Bernard', 'chloe.bernard@example.com');

CREATE TABLE IF NOT EXISTS clients_sink (
    id INTEGER PRIMARY KEY,
    nom VARCHAR(100),
    email VARCHAR(150),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
