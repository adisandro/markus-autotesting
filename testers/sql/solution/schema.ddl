CREATE TABLE table1 (
  id integer PRIMARY KEY,
  word varchar(50)
);

CREATE TABLE table2 (
  id integer PRIMARY KEY,
  number double precision NOT NULL,
  foreign_id integer NOT NULL REFERENCES table1
);