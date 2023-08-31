CREATE TABLE IF NOT EXISTS public.users (
    user_id text NOT NULL,
    username text UNIQUE,
    hashed_password text NOT NULL,
    fullname text NOT NULL,
    email text UNIQUE,
    scopes text array,
    is_banned boolean NOT NULL DEFAULT 'false',
    is_admin boolean NOT NULL DEFAULT 'false'
);

CREATE TABLE IF NOT EXISTS public.urls (
    url_id serial PRIMARY KEY,
    url_key text UNIQUE,
    secret_key text UNIQUE,
    target_url text NOT NULL,
    is_active boolean NOT NULL DEFAULT 'true',
    clicks int8 NOT NULL DEFAULT 0,
    created_at timestamp NOT NULL DEFAULT NOW()
);

INSERT INTO users VALUES (
    '01H8YA58JAE536F5XGMBM5NGMX',
    'admin',
    'secret_hash_placeholder',
    'Mr. Admin',
    'admin@localhost',
    ARRAY ['admin'],
    'false',
    'true'
) ON CONFLICT DO NOTHING; -- only insert if not exists
