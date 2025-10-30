CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    
    -- password_hash: Texto para guardar la contraseña encriptada.
    -- Le damos espacio (255) para algoritmos de hash como bcrypt.
    password_hash VARCHAR(255) NOT NULL
);

INSERT INTO users (username, password_hash)
VALUES ('admin', 'scrypt:32768:8:1$6sAAfUny2WpP5YkI$d48ff48172c43492c6c228d5123a1585ed8c49621a6d9d70bca050f39a0951f23ca80b66854ef7c96aa1bf900468c526ee3146e2b741be7b058181394c7eed18');
