CREATE EXTENSION vector;

CREATE DATABASE IF NOT EXISTS icognition
	WITH
    OWNER = root
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

CREATE SCHEMA IF NOT EXISTS wikidata;


CREATE TABLE IF NOT EXISTS wikidata.raw_items (
  id int,
  label varchar(200),
  description text,
  page_id int,
  views int,
  inlinks int
);

CREATE TABLE IF NOT EXISTS wikidata.aliases (
  id serial PRIMARY KEY,
  alias text NOT NULL,
  lcase_alias text NOT NULL
);

CREATE TABLE IF NOT EXISTS wikidata.items_vectors (
  id serial PRIMARY KEY,
  label_desc text NOT NULL,
  keywords text NOT NULL,
  label_desc_vec vector(384) NOT NULL,
  keywords_vec vector(384) NOT NULL
);

\copy wikidata.items(id, wikipedia_page_id, text, embedding) FROM 'done_embeddings_0_500000.csv' DELIMITER ',' CSV HEADER

CREATE USER app WITH PASSWORD '2214';
GRANT ALL ON DATABASE icog_db TO app;
GRANT pg_read_all_data TO app;
GRANT pg_write_all_data TO app;
GRANT USAGE ON SCHEMA public TO app;

CREATE SCHEMA IF NOT EXISTS bmks;
GRANT ALL privileges ON SCHEMA bmks TO app;


CREATE TABLE IF NOT EXISTS wikidata.items_label_desc_vectors (
  id serial PRIMARY KEY,
  page_id float, 
  label_desc text NOT NULL,
  label_desc_vec vector(384) NOT NULL
);
GRANT ALL privileges ON TABLE wikidata.items_label_desc_vectors TO app;

INSERT INTO wikidata.items (id, label, description, wikipedia_page_id, views, links)
(SELECT id, label, description, page_id, views, inlinks 
FROM wikidata.raw_items 
WHERE label is NOT NULL OR LENGTH(label) < 30);