-- The official entrypoint initially grants schema-wide privileges to MYSQL_USER.
-- Restrict the application before the DB healthcheck can succeed.
-- Revoke account-wide: the entrypoint escapes underscores in database grants.
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'group08_app'@'%';
GRANT SELECT, INSERT ON lab_config.orders TO 'group08_app'@'%';
