-- Creates one microservice's database and its own login role on a shared PostgreSQL
-- instance. Run once per service and stage, as the instance admin:
--   psql -v ON_ERROR_STOP=1 -v service_db=<db> -v service_user=<user> \
--        -v service_password=<password> -f create_service_database.sql
CREATE ROLE :"service_user" LOGIN PASSWORD :'service_password' CONNECTION LIMIT 20;

-- PostgreSQL 16: to make another role the owner of a new database, the admin must be
-- able to SET ROLE to it.
GRANT :"service_user" TO CURRENT_USER;

CREATE DATABASE :"service_db" OWNER :"service_user";
REVOKE ALL ON DATABASE :"service_db" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"service_db" TO :"service_user";
