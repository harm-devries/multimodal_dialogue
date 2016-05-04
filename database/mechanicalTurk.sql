--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: answer_type; Type: TYPE; Schema: public; Owner: fstrub
--

CREATE TYPE answer_type AS ENUM (
    'Yes',
    'No',
    'N/A'
);


ALTER TYPE answer_type OWNER TO fstrub;

--
-- Name: guess_order(); Type: FUNCTION; Schema: public; Owner: mkadmin
--

CREATE FUNCTION guess_order() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
    new.order:= next_guess(new.dialogue_id);
    return new;
end $$;


ALTER FUNCTION public.guess_order() OWNER TO mkadmin;

--
-- Name: next_guess(integer); Type: FUNCTION; Schema: public; Owner: mkadmin
--

CREATE FUNCTION next_guess(integer) RETURNS integer
    LANGUAGE sql
    AS $_$
SELECT COALESCE(((SELECT MAX(q.order) FROM guess AS q WHERE q.dialogue_id = $1) +1), 0)  ;
$_$;


ALTER FUNCTION public.next_guess(integer) OWNER TO mkadmin;

--
-- Name: next_order(integer); Type: FUNCTION; Schema: public; Owner: mkadmin
--

CREATE FUNCTION next_order(integer) RETURNS integer
    LANGUAGE sql
    AS $_$
SELECT COALESCE(((SELECT MAX(q.order) FROM question AS q WHERE q.dialogue_id = $1) +1), 0)  ;
$_$;


ALTER FUNCTION public.next_order(integer) OWNER TO mkadmin;

--
-- Name: next_order2(integer); Type: FUNCTION; Schema: public; Owner: mkadmin
--

CREATE FUNCTION next_order2(integer) RETURNS integer
    LANGUAGE sql
    AS $_$
SELECT 1 + (SELECT MAX(q.order) FROM question AS q WHERE q.dialogue_id = $1);
$_$;


ALTER FUNCTION public.next_order2(integer) OWNER TO mkadmin;

--
-- Name: question_order(); Type: FUNCTION; Schema: public; Owner: mkadmin
--

CREATE FUNCTION question_order() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
    new.order:= next_order(new.dialogue_id);
    return new;
end $$;


ALTER FUNCTION public.question_order() OWNER TO mkadmin;

--
-- Name: answer_seq; Type: SEQUENCE; Schema: public; Owner: mkadmin
--

CREATE SEQUENCE answer_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE answer_seq OWNER TO mkadmin;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: answer; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE answer (
    answer_id integer DEFAULT nextval('answer_seq'::regclass) NOT NULL,
    question_id integer NOT NULL,
    content answer_type NOT NULL,
    "timestamp" time without time zone DEFAULT now() NOT NULL
);


ALTER TABLE answer OWNER TO mkadmin;

--
-- Name: dialogue_seq; Type: SEQUENCE; Schema: public; Owner: mkadmin
--

CREATE SEQUENCE dialogue_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE dialogue_seq OWNER TO mkadmin;

--
-- Name: dialogue; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE dialogue (
    dialogue_id integer DEFAULT nextval('dialogue_seq'::regclass) NOT NULL,
    picture_id integer NOT NULL,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL,
    object_id bigint,
    oracle_hit_id integer,
    questioner_hit_id integer
);


ALTER TABLE dialogue OWNER TO mkadmin;

--
-- Name: guess_seq; Type: SEQUENCE; Schema: public; Owner: mkadmin
--

CREATE SEQUENCE guess_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE guess_seq OWNER TO mkadmin;

--
-- Name: guess; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE guess (
    guess_id integer DEFAULT nextval('guess_seq'::regclass) NOT NULL,
    "order" integer NOT NULL,
    object_id bigint NOT NULL,
    "timestamp" timestamp without time zone DEFAULT now(),
    dialogue_id integer NOT NULL
);


ALTER TABLE guess OWNER TO mkadmin;

--
-- Name: hit_seq; Type: SEQUENCE; Schema: public; Owner: mkadmin
--

CREATE SEQUENCE hit_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE hit_seq OWNER TO mkadmin;

--
-- Name: hit; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE hit (
    hit_id integer DEFAULT nextval('hit_seq'::regclass) NOT NULL,
    worker_id integer NOT NULL,
    is_valid boolean DEFAULT false NOT NULL,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE hit OWNER TO mkadmin;

--
-- Name: object_seq; Type: SEQUENCE; Schema: public; Owner: mkadmin
--

CREATE SEQUENCE object_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE object_seq OWNER TO mkadmin;

--
-- Name: object; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE object (
    object_id bigint DEFAULT nextval('object_seq'::regclass) NOT NULL,
    picture_id integer NOT NULL,
    category_id integer NOT NULL,
    segment jsonb NOT NULL,
    bbox jsonb,
    is_crowd boolean DEFAULT false NOT NULL,
    area numeric DEFAULT 0 NOT NULL
);


ALTER TABLE object OWNER TO mkadmin;

--
-- Name: object_category; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE object_category (
    category_id numeric NOT NULL,
    name character varying(50),
    supercategory_id integer NOT NULL
);


ALTER TABLE object_category OWNER TO mkadmin;

--
-- Name: object_supercategory; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE object_supercategory (
    supercategory_id integer NOT NULL,
    name character varying(50)
);


ALTER TABLE object_supercategory OWNER TO mkadmin;

--
-- Name: picture_seq; Type: SEQUENCE; Schema: public; Owner: mkadmin
--

CREATE SEQUENCE picture_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE picture_seq OWNER TO mkadmin;

--
-- Name: picture; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE picture (
    picture_id integer NOT NULL,
    flickr_url text,
    file_name character varying(255),
    height integer,
    width integer,
    coco_url text NOT NULL,
    serial_id integer DEFAULT nextval('picture_seq'::regclass) NOT NULL,
    difficulty integer DEFAULT 1 NOT NULL
);


ALTER TABLE picture OWNER TO mkadmin;

--
-- Name: player; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE player (
    name character varying(255),
    score integer DEFAULT 0
);


ALTER TABLE player OWNER TO mkadmin;

--
-- Name: question_seq; Type: SEQUENCE; Schema: public; Owner: mkadmin
--

CREATE SEQUENCE question_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE question_seq OWNER TO mkadmin;

--
-- Name: question; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE question (
    question_id integer DEFAULT nextval('question_seq'::regclass) NOT NULL,
    dialogue_id integer NOT NULL,
    content text,
    "order" integer,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE question OWNER TO mkadmin;

--
-- Name: report_dialogue; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE report_dialogue (
    report_dialogue_id integer NOT NULL,
    dialogue_id integer NOT NULL,
    worker_id integer NOT NULL,
    picture_too_hard boolean DEFAULT false NOT NULL,
    object_too_hard boolean DEFAULT false NOT NULL,
    content text,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL,
    from_oracle boolean NOT NULL
);


ALTER TABLE report_dialogue OWNER TO mkadmin;

--
-- Name: report_dialogue_report_dialogue_id_seq; Type: SEQUENCE; Schema: public; Owner: mkadmin
--

CREATE SEQUENCE report_dialogue_report_dialogue_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE report_dialogue_report_dialogue_id_seq OWNER TO mkadmin;

--
-- Name: report_dialogue_report_dialogue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkadmin
--

ALTER SEQUENCE report_dialogue_report_dialogue_id_seq OWNED BY report_dialogue.report_dialogue_id;


--
-- Name: report_worker; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE report_worker (
    report_worker_id integer NOT NULL,
    dialogue_id integer NOT NULL,
    from_worker_id integer,
    to_worker_id integer NOT NULL,
    from_oracle boolean NOT NULL,
    too_slow boolean DEFAULT false NOT NULL,
    harassment boolean DEFAULT false NOT NULL,
    bad_player boolean DEFAULT false NOT NULL,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL,
    content text
);


ALTER TABLE report_worker OWNER TO mkadmin;

--
-- Name: report_worker_report_worker_id_seq; Type: SEQUENCE; Schema: public; Owner: mkadmin
--

CREATE SEQUENCE report_worker_report_worker_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE report_worker_report_worker_id_seq OWNER TO mkadmin;

--
-- Name: report_worker_report_worker_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkadmin
--

ALTER SEQUENCE report_worker_report_worker_id_seq OWNED BY report_worker.report_worker_id;


--
-- Name: worker; Type: TABLE; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE TABLE worker (
    worker_id integer NOT NULL
);


ALTER TABLE worker OWNER TO mkadmin;

--
-- Name: report_dialogue_id; Type: DEFAULT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY report_dialogue ALTER COLUMN report_dialogue_id SET DEFAULT nextval('report_dialogue_report_dialogue_id_seq'::regclass);


--
-- Name: report_worker_id; Type: DEFAULT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY report_worker ALTER COLUMN report_worker_id SET DEFAULT nextval('report_worker_report_worker_id_seq'::regclass);


--
-- Data for Name: answer; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY answer (answer_id, question_id, content, "timestamp") FROM stdin;
\.


--
-- Name: answer_seq; Type: SEQUENCE SET; Schema: public; Owner: mkadmin
--

SELECT pg_catalog.setval('answer_seq', 1, false);


--
-- Data for Name: dialogue; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY dialogue (dialogue_id, picture_id, "timestamp", object_id, oracle_hit_id, questioner_hit_id) FROM stdin;
\.


--
-- Name: dialogue_seq; Type: SEQUENCE SET; Schema: public; Owner: mkadmin
--

SELECT pg_catalog.setval('dialogue_seq', 1, false);


--
-- Data for Name: guess; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY guess (guess_id, "order", object_id, "timestamp", dialogue_id) FROM stdin;
\.


--
-- Name: guess_seq; Type: SEQUENCE SET; Schema: public; Owner: mkadmin
--

SELECT pg_catalog.setval('guess_seq', 1, false);


--
-- Data for Name: hit; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY hit (hit_id, worker_id, is_valid, "timestamp") FROM stdin;
\.


--
-- Name: hit_seq; Type: SEQUENCE SET; Schema: public; Owner: mkadmin
--

SELECT pg_catalog.setval('hit_seq', 1, false);


--
-- Data for Name: object; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY object (object_id, picture_id, category_id, segment, bbox, is_crowd, area) FROM stdin;
\.


--
-- Data for Name: object_category; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY object_category (category_id, name, supercategory_id) FROM stdin;
\.


--
-- Name: object_seq; Type: SEQUENCE SET; Schema: public; Owner: mkadmin
--

SELECT pg_catalog.setval('object_seq', 1, false);


--
-- Data for Name: object_supercategory; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY object_supercategory (supercategory_id, name) FROM stdin;
\.


--
-- Data for Name: picture; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY picture (picture_id, flickr_url, file_name, height, width, coco_url, serial_id, difficulty) FROM stdin;
\.


--
-- Name: picture_seq; Type: SEQUENCE SET; Schema: public; Owner: mkadmin
--

SELECT pg_catalog.setval('picture_seq', 1, false);


--
-- Data for Name: player; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY player (name, score) FROM stdin;
\.


--
-- Data for Name: question; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY question (question_id, dialogue_id, content, "order", "timestamp") FROM stdin;
\.


--
-- Name: question_seq; Type: SEQUENCE SET; Schema: public; Owner: mkadmin
--

SELECT pg_catalog.setval('question_seq', 1, false);


--
-- Data for Name: report_dialogue; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY report_dialogue (report_dialogue_id, dialogue_id, worker_id, picture_too_hard, object_too_hard, content, "timestamp", from_oracle) FROM stdin;
\.


--
-- Name: report_dialogue_report_dialogue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mkadmin
--

SELECT pg_catalog.setval('report_dialogue_report_dialogue_id_seq', 1, false);


--
-- Data for Name: report_worker; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY report_worker (report_worker_id, dialogue_id, from_worker_id, to_worker_id, from_oracle, too_slow, harassment, bad_player, "timestamp", content) FROM stdin;
\.


--
-- Name: report_worker_report_worker_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mkadmin
--

SELECT pg_catalog.setval('report_worker_report_worker_id_seq', 1, false);


--
-- Data for Name: worker; Type: TABLE DATA; Schema: public; Owner: mkadmin
--

COPY worker (worker_id) FROM stdin;
1
10
20
\.


--
-- Name: Answer_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY answer
    ADD CONSTRAINT "Answer_pkey" PRIMARY KEY (answer_id);


--
-- Name: Dialogue_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY dialogue
    ADD CONSTRAINT "Dialogue_pkey" PRIMARY KEY (dialogue_id);


--
-- Name: Hit_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY hit
    ADD CONSTRAINT "Hit_pkey" PRIMARY KEY (hit_id);


--
-- Name: Object_category_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY object_category
    ADD CONSTRAINT "Object_category_pkey" PRIMARY KEY (category_id);


--
-- Name: Object_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY object
    ADD CONSTRAINT "Object_pkey" PRIMARY KEY (object_id);


--
-- Name: Picture_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY picture
    ADD CONSTRAINT "Picture_pkey" PRIMARY KEY (picture_id);


--
-- Name: Question_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY question
    ADD CONSTRAINT "Question_pkey" PRIMARY KEY (question_id);


--
-- Name: answer_question_id_key; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY answer
    ADD CONSTRAINT answer_question_id_key UNIQUE (question_id);


--
-- Name: guess_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY guess
    ADD CONSTRAINT guess_pkey PRIMARY KEY (guess_id);


--
-- Name: object_supercategory_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY object_supercategory
    ADD CONSTRAINT object_supercategory_pkey PRIMARY KEY (supercategory_id);


--
-- Name: picture_serial_id_key; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY picture
    ADD CONSTRAINT picture_serial_id_key UNIQUE (serial_id);


--
-- Name: report_dialogue_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY report_dialogue
    ADD CONSTRAINT report_dialogue_pkey PRIMARY KEY (report_dialogue_id);


--
-- Name: report_worker_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY report_worker
    ADD CONSTRAINT report_worker_pkey PRIMARY KEY (report_worker_id);


--
-- Name: worker_pkey; Type: CONSTRAINT; Schema: public; Owner: mkadmin; Tablespace: 
--

ALTER TABLE ONLY worker
    ADD CONSTRAINT worker_pkey PRIMARY KEY (worker_id);


--
-- Name: fki_answer_to_exchange_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_answer_to_exchange_fkey ON answer USING btree (question_id);


--
-- Name: fki_category_to_supercategory_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_category_to_supercategory_fkey ON object_category USING btree (supercategory_id);


--
-- Name: fki_dialogue_to_guess_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_dialogue_to_guess_fkey ON dialogue USING btree (object_id);


--
-- Name: fki_dialogue_to_picture_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_dialogue_to_picture_fkey ON dialogue USING btree (picture_id);


--
-- Name: fki_guess_to_dialogue_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_guess_to_dialogue_fkey ON guess USING btree (dialogue_id);


--
-- Name: fki_guess_to_object_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_guess_to_object_fkey ON guess USING btree (object_id);


--
-- Name: fki_hit_to_worker_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_hit_to_worker_fkey ON hit USING btree (worker_id);


--
-- Name: fki_object_to_category_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_object_to_category_fkey ON object USING btree (category_id);


--
-- Name: fki_object_to_picture_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_object_to_picture_fkey ON object USING btree (picture_id);


--
-- Name: fki_oracle_to_worker_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_oracle_to_worker_fkey ON dialogue USING btree (oracle_hit_id);


--
-- Name: fki_question_to_exchange_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_question_to_exchange_fkey ON question USING btree (dialogue_id);


--
-- Name: fki_questioner_to_worker_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_questioner_to_worker_fkey ON dialogue USING btree (questioner_hit_id);


--
-- Name: fki_report_dialogue_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_report_dialogue_fkey ON report_dialogue USING btree (dialogue_id);


--
-- Name: fki_report_dialogue_from_worker_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_report_dialogue_from_worker_fkey ON report_dialogue USING btree (worker_id);


--
-- Name: fki_report_from_worker_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_report_from_worker_fkey ON report_worker USING btree (from_worker_id);


--
-- Name: fki_report_to_worker_fkey; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX fki_report_to_worker_fkey ON report_worker USING btree (to_worker_id);


--
-- Name: serial_index; Type: INDEX; Schema: public; Owner: mkadmin; Tablespace: 
--

CREATE INDEX serial_index ON picture USING btree (serial_id);


--
-- Name: guess_order; Type: TRIGGER; Schema: public; Owner: mkadmin
--

CREATE TRIGGER guess_order BEFORE INSERT OR UPDATE ON guess FOR EACH ROW EXECUTE PROCEDURE guess_order();


--
-- Name: question_order; Type: TRIGGER; Schema: public; Owner: mkadmin
--

CREATE TRIGGER question_order BEFORE INSERT OR UPDATE ON question FOR EACH ROW EXECUTE PROCEDURE question_order();


--
-- Name: answer_to_question_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY answer
    ADD CONSTRAINT answer_to_question_fkey FOREIGN KEY (question_id) REFERENCES question(question_id);


--
-- Name: category_to_supercategory_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY object_category
    ADD CONSTRAINT category_to_supercategory_fkey FOREIGN KEY (supercategory_id) REFERENCES object_supercategory(supercategory_id);


--
-- Name: dialogue_to_guess_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY dialogue
    ADD CONSTRAINT dialogue_to_guess_fkey FOREIGN KEY (object_id) REFERENCES object(object_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: dialogue_to_picture_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY dialogue
    ADD CONSTRAINT dialogue_to_picture_fkey FOREIGN KEY (picture_id) REFERENCES picture(picture_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: guess_to_dialogue_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY guess
    ADD CONSTRAINT guess_to_dialogue_fkey FOREIGN KEY (dialogue_id) REFERENCES dialogue(dialogue_id);


--
-- Name: guess_to_object_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY guess
    ADD CONSTRAINT guess_to_object_fkey FOREIGN KEY (object_id) REFERENCES object(object_id);


--
-- Name: hit_to_worker_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY hit
    ADD CONSTRAINT hit_to_worker_fkey FOREIGN KEY (worker_id) REFERENCES worker(worker_id);


--
-- Name: object_to_category_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY object
    ADD CONSTRAINT object_to_category_fkey FOREIGN KEY (category_id) REFERENCES object_category(category_id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: object_to_picture_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY object
    ADD CONSTRAINT object_to_picture_fkey FOREIGN KEY (picture_id) REFERENCES picture(picture_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: oracle_to_hit_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY dialogue
    ADD CONSTRAINT oracle_to_hit_fkey FOREIGN KEY (oracle_hit_id) REFERENCES hit(hit_id);


--
-- Name: question_to_dialogue_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY question
    ADD CONSTRAINT question_to_dialogue_fkey FOREIGN KEY (dialogue_id) REFERENCES dialogue(dialogue_id);


--
-- Name: questioner_to_hit_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY dialogue
    ADD CONSTRAINT questioner_to_hit_fkey FOREIGN KEY (questioner_hit_id) REFERENCES hit(hit_id);


--
-- Name: report_dialogue_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY report_dialogue
    ADD CONSTRAINT report_dialogue_fkey FOREIGN KEY (dialogue_id) REFERENCES dialogue(dialogue_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: report_dialogue_from_worker_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY report_dialogue
    ADD CONSTRAINT report_dialogue_from_worker_fkey FOREIGN KEY (worker_id) REFERENCES worker(worker_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: report_from_worker_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY report_worker
    ADD CONSTRAINT report_from_worker_fkey FOREIGN KEY (from_worker_id) REFERENCES worker(worker_id);


--
-- Name: report_to_worker_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mkadmin
--

ALTER TABLE ONLY report_worker
    ADD CONSTRAINT report_to_worker_fkey FOREIGN KEY (to_worker_id) REFERENCES worker(worker_id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: answer; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE answer FROM PUBLIC;
REVOKE ALL ON TABLE answer FROM mkadmin;
GRANT ALL ON TABLE answer TO mkadmin;
GRANT SELECT,INSERT,UPDATE ON TABLE answer TO mkuser;


--
-- Name: dialogue; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE dialogue FROM PUBLIC;
REVOKE ALL ON TABLE dialogue FROM mkadmin;
GRANT ALL ON TABLE dialogue TO mkadmin;
GRANT SELECT,INSERT,UPDATE ON TABLE dialogue TO mkuser;


--
-- Name: guess; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE guess FROM PUBLIC;
REVOKE ALL ON TABLE guess FROM mkadmin;
GRANT ALL ON TABLE guess TO mkadmin;
GRANT SELECT,INSERT ON TABLE guess TO mkuser;


--
-- Name: hit; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE hit FROM PUBLIC;
REVOKE ALL ON TABLE hit FROM mkadmin;
GRANT ALL ON TABLE hit TO mkadmin;
GRANT SELECT,INSERT ON TABLE hit TO mkuser;


--
-- Name: object; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE object FROM PUBLIC;
REVOKE ALL ON TABLE object FROM mkadmin;
GRANT ALL ON TABLE object TO mkadmin;


--
-- Name: object_category; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE object_category FROM PUBLIC;
REVOKE ALL ON TABLE object_category FROM mkadmin;
GRANT ALL ON TABLE object_category TO mkadmin;


--
-- Name: object_supercategory; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE object_supercategory FROM PUBLIC;
REVOKE ALL ON TABLE object_supercategory FROM mkadmin;
GRANT ALL ON TABLE object_supercategory TO mkadmin;


--
-- Name: picture; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE picture FROM PUBLIC;
REVOKE ALL ON TABLE picture FROM mkadmin;
GRANT ALL ON TABLE picture TO mkadmin;


--
-- Name: player; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE player FROM PUBLIC;
REVOKE ALL ON TABLE player FROM mkadmin;
GRANT ALL ON TABLE player TO mkadmin;
GRANT SELECT,INSERT ON TABLE player TO mkuser;


--
-- Name: question; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE question FROM PUBLIC;
REVOKE ALL ON TABLE question FROM mkadmin;
GRANT ALL ON TABLE question TO mkadmin;
GRANT SELECT,INSERT ON TABLE question TO mkuser;


--
-- Name: report_dialogue; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE report_dialogue FROM PUBLIC;
REVOKE ALL ON TABLE report_dialogue FROM mkadmin;
GRANT ALL ON TABLE report_dialogue TO mkadmin;
GRANT SELECT,INSERT ON TABLE report_dialogue TO mkuser;


--
-- Name: report_worker; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE report_worker FROM PUBLIC;
REVOKE ALL ON TABLE report_worker FROM mkadmin;
GRANT ALL ON TABLE report_worker TO mkadmin;
GRANT SELECT,INSERT ON TABLE report_worker TO mkuser;


--
-- Name: worker; Type: ACL; Schema: public; Owner: mkadmin
--

REVOKE ALL ON TABLE worker FROM PUBLIC;
REVOKE ALL ON TABLE worker FROM mkadmin;
GRANT ALL ON TABLE worker TO mkadmin;
GRANT SELECT,INSERT ON TABLE worker TO mkuser;


--
-- PostgreSQL database dump complete
--

