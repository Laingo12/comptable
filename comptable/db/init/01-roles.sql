-- Création des rôles applicatifs (exécuté par l'entrypoint PostgreSQL en superuser).
-- Les mots de passe proviennent de l'environnement du conteneur / de la session psql.
-- Idempotent : ne recrée pas un rôle existant.

\getenv db_name       POSTGRES_DB
\getenv owner_user     POSTGRES_OWNER_USER
\getenv owner_pwd      POSTGRES_OWNER_PASSWORD
\getenv app_user       POSTGRES_APP_USER
\getenv app_pwd        POSTGRES_APP_PASSWORD

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'owner_user', :'owner_pwd')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'owner_user')
\gexec

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'app_user', :'app_pwd')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app_user')
\gexec

SELECT format('ALTER DATABASE %I OWNER TO %I', :'db_name', :'owner_user')
\gexec

SELECT format('REVOKE ALL ON DATABASE %I FROM PUBLIC', :'db_name')
\gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO %I, %I', :'db_name', :'owner_user', :'app_user')
\gexec

SELECT format('ALTER SCHEMA public OWNER TO %I', :'owner_user')
\gexec

SELECT format('REVOKE ALL ON SCHEMA public FROM PUBLIC')
\gexec

SELECT format('GRANT USAGE ON SCHEMA public TO %I, %I', :'owner_user', :'app_user')
\gexec

SELECT format('ALTER DATABASE %I SET timezone = %L', :'db_name', 'Indian/Antananarivo')
\gexec