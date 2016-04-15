﻿TRUNCATE object CASCADE;
TRUNCATE object_category CASCADE;
TRUNCATE object_supercategory CASCADE;
TRUNCATE dialogue CASCADE;
TRUNCATE picture CASCADE;
TRUNCATE question CASCADE;
TRUNCATE answer CASCADE;
TRUNCATE hit CASCADE;
TRUNCATE guess CASCADE;

ALTER SEQUENCE answer_seq RESTART;
ALTER SEQUENCE dialogue_seq RESTART;
ALTER SEQUENCE hit_seq RESTART;
ALTER SEQUENCE object_seq RESTART;
ALTER SEQUENCE picture_seq RESTART;
ALTER SEQUENCE question_seq RESTART;
ALTER SEQUENCE guess_seq RESTART;

