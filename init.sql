CREATE DATABASE default_db;
CREATE DATABASE test_db;
CREATE user test with encrypted password 'test';
CREATE user local with encrypted password 'local';
GRANT ALL PRIVILEGES ON DATABASE "test_db" to test;
GRANT ALL PRIVILEGES ON DATABASE "default_db" to local;
