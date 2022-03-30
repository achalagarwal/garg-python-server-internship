CREATE DATABASE default_db;
CREATE DATABASE test_db;
CREATE user test_user with encrypted password 'test_password';
CREATE user default_user with encrypted password 'default_password';
GRANT ALL PRIVILEGES ON DATABASE "test_db" to test_user;
GRANT ALL PRIVILEGES ON DATABASE "default_db" to default_user;
