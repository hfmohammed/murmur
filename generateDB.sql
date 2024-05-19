-- Let's drop the tables in case they exist from previous runs
DROP TABLE IF EXISTS retweets;
DROP TABLE IF EXISTS mentions;
DROP TABLE IF EXISTS hashtags;
DROP TABLE IF EXISTS tweets;
DROP TABLE IF EXISTS follows;
DROP TABLE IF EXISTS users;

-- Create the tables
CREATE TABLE users (
  usr         CHAR(100),
  pwd         CHAR(100),
  name        CHAR(100),
  email       CHAR(100),
  city        CHAR(100),
  PRIMARY KEY (usr)
);

CREATE TABLE follows (
  flwer       CHAR(100),
  flwee       CHAR(100),
  start_date  DATE,
  PRIMARY KEY (flwer, flwee),
  FOREIGN KEY (flwer) REFERENCES users,
  FOREIGN KEY (flwee) REFERENCES users
);

CREATE TABLE tweets (
  tid         INT,
  writer      CHAR(100),
  tdate       DATE,
  text        CHAR(500),
  replyto     INT,
  PRIMARY KEY (tid),
  FOREIGN KEY (writer) REFERENCES users,
  FOREIGN KEY (replyto) REFERENCES tweets
);

CREATE TABLE hashtags (
  term        CHAR(100),
  PRIMARY KEY (term)
);

CREATE TABLE mentions (
  tid         INT,
  term        CHAR(100),
  PRIMARY KEY (tid, term),
  FOREIGN KEY (tid) REFERENCES tweets,
  FOREIGN KEY (term) REFERENCES hashtags
);

CREATE TABLE retweets (
  usr         CHAR(100),
  tid         INT,
  rdate       DATE,
  PRIMARY KEY (usr, tid),
  FOREIGN KEY (usr) REFERENCES users,
  FOREIGN KEY (tid) REFERENCES tweets
);

-- Let's enforce the foreign keys
PRAGMA FOREIGN_KEYS = ON;

-- Application 1
INSERT INTO users VALUES ('10', 'aaa', 'validusr', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('11', 'aaa', 'existedusr', 'usr@email.ca', 'Rome');
-- Case 2.3
INSERT INTO users VALUES ('1', 'aaa', 'usr101', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('2', 'aaa', '101follow102', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('3', 'aaa', '101follow103', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('4', 'aaa', '101notfollow104', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('5', 'aaa', '101notfollow105', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('6', 'aaa', '101notfollow106', 'usr@email.ca', 'Rome');

INSERT INTO users VALUES ('7', 'aaa', 'usr107', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('8', 'aaa', 'usr108', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('9', 'aaa', 'usr109', 'usr@email.ca', 'Rome');

INSERT INTO follows VALUES ('1', '2', '2022-09-01');
INSERT INTO follows VALUES ('1', '3', '2022-09-01');

-- First 5
INSERT INTO tweets VALUES (10201, '2', '2022-08-21', 'tweet1 of usr101 followee', NULL);
INSERT INTO tweets VALUES (10202, '2', '2022-08-20', 'tweet2 of usr101 followee', NULL);
INSERT INTO tweets VALUES (10203, '2', '2022-08-19', 'tweet3 of usr101 followee', NULL);
INSERT INTO tweets VALUES (10301, '3', '2022-08-18', 'tweet4 of usr101 followee', NULL);
INSERT INTO tweets VALUES (10302, '3', '2022-08-17', 'tweet5 of usr101 followee', NULL);

INSERT INTO tweets VALUES (10401, '4', '2020-08-02', 'retweet7 of usr101 followee', NULL);
INSERT INTO tweets VALUES (10402, '4', '2020-08-03', 'retweet8 of usr101 followee', NULL);
INSERT INTO tweets VALUES (10403, '4', '2020-08-04', 'retweet10 of usr101 followee', NULL);

-- Second 5
INSERT INTO tweets VALUES (10303, '3', '2022-08-16', 'tweet6 of usr101 followee', NULL);
INSERT INTO retweets VALUES ('3', 10401, '2022-08-15');
INSERT INTO retweets VALUES ('3', 10402, '2022-08-14');
INSERT INTO tweets VALUES (10304, '3', '2022-08-13', 'tweet9 of usr101 followee', NULL);
INSERT INTO retweets VALUES ('2', 10403, '2022-08-12');

-- 3 retweets for tweet9
INSERT INTO retweets VALUES ('6', 10304, '2022-08-14');
INSERT INTO retweets VALUES ('5', 10304, '2022-08-14');
INSERT INTO retweets VALUES ('4', 10304, '2022-08-14');

-- 6 replies for tweet9
INSERT INTO tweets VALUES (10501, '5', '2022-08-14', 'reply501 to tweet9', 10304);
INSERT INTO tweets VALUES (10502, '5', '2022-08-14', 'reply502 to tweet9', 10304);
INSERT INTO tweets VALUES (10503, '5', '2022-08-14', 'reply503 to tweet9', 10304);
INSERT INTO tweets VALUES (10601, '6', '2022-08-14', 'reply601 to tweet9', 10304);
INSERT INTO tweets VALUES (10602, '6', '2022-08-14', 'reply602 to tweet9', 10304);
INSERT INTO tweets VALUES (10603, '6', '2022-08-14', 'reply603 to tweet9', 10304);

-- Application 2
INSERT INTO hashtags VALUES ('edmonton');
INSERT INTO hashtags VALUES ('jobs');
INSERT INTO hashtags VALUES ('oilers');

-- Search hashtag Edmonton
-- Search context Edmonton
INSERT INTO tweets VALUES (10701, '7', '2022-08-15', 'tweet1 with keyword hashtag', NULL);
INSERT INTO tweets VALUES (10702, '7', '2022-08-14', 'tweet2 with keyword hashtag Edmonton', NULL);
INSERT INTO tweets VALUES (10703, '7', '2022-08-13', 'tweet3 with keyword hashtag edmonton', NULL);
INSERT INTO mentions VALUES (10701, 'edmonton');
INSERT INTO mentions VALUES (10702, 'edmonton');
INSERT INTO mentions VALUES (10703, 'edmonton');

INSERT INTO tweets VALUES (10704, '7', '2022-08-12', 'tweet4 without keyword hashtag edmonton but oilers', NULL);
INSERT INTO tweets VALUES (10705, '7', '2022-08-11', 'tweet5 with context Edmonton and hashtag jobs', NULL);
INSERT INTO mentions VALUES (10704, 'oilers');
INSERT INTO mentions VALUES (10705, 'jobs');

INSERT INTO tweets VALUES (10706, '7', '2022-08-10', 'tweet6 with context Edmonton', NULL);
INSERT INTO tweets VALUES (10707, '7', '2022-08-09', 'tweet7 with context Edmonton', NULL);
INSERT INTO tweets VALUES (10708, '7', '2022-08-08', 'tweet8 with context Edmonton', NULL);

INSERT INTO tweets VALUES (10709, '7', '2022-08-07', 'tweet9 with context oilers', NULL);
INSERT INTO tweets VALUES (10710, '7', '2022-08-06', 'tweet10 with context jobs', NULL);

-- See statistic tweet10707
-- 2 retweets for tweet10707
INSERT INTO retweets VALUES ('8', 10707, '2022-08-14');
INSERT INTO retweets VALUES ('9', 10707, '2022-08-14');

-- 6 replies for tweet10707
INSERT INTO tweets VALUES (10801, '8', '2022-08-14', 'reply801 to tweet7', 10707);
INSERT INTO tweets VALUES (10802, '8', '2022-08-14', 'reply802 to tweet7', 10707);
INSERT INTO tweets VALUES (10803, '8', '2022-08-14', 'reply803 to tweet7', 10707);
INSERT INTO tweets VALUES (10901, '9', '2022-08-14', 'reply901 to tweet7', 10707);
INSERT INTO tweets VALUES (10902, '9', '2022-08-14', 'reply902 to tweet7', 10707);
INSERT INTO tweets VALUES (10903, '9', '2022-08-14', 'reply903 to tweet7', 10707);

-- Application 3
INSERT INTO users VALUES ('21', 'aaa', 'usr121ABCD', 'usr@email.ca', 'UVWXYZ');
INSERT INTO users VALUES ('22', 'aaa', 'usr122ABCDE', 'usr@email.ca', 'VWXYZ');
INSERT INTO users VALUES ('23', 'aaa', 'usr123ABCDEF', 'usr@email.ca', 'WXYZ');
INSERT INTO users VALUES ('24', 'aaa', 'usr124ABCDEDG', 'usr@email.ca', 'XYZ');

INSERT INTO users VALUES ('25', 'aaa', 'usr125JKL', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('26', 'aaa', 'usr126JKLM', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('27', 'aaa', 'usr127JKLMN', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('28', 'aaa', 'usr128JKLMNO', 'usr@email.ca', 'JKLMNOP');
INSERT INTO users VALUES ('29', 'aaa', 'usr129', 'usr@email.ca', 'JKLM');
INSERT INTO users VALUES ('30', 'aaa', 'usr130', 'usr@email.ca', 'JKLMN');
INSERT INTO users VALUES ('31', 'aaa', 'usr131', 'usr@email.ca', 'JKLMNO');

-- 129 follows 125,126,127,128
INSERT INTO follows VALUES ('29', '25', '2022-09-01');
INSERT INTO follows VALUES ('29', '26', '2022-09-01');
INSERT INTO follows VALUES ('29', '27', '2022-09-01');
INSERT INTO follows VALUES ('29', '28', '2022-09-01');

-- 130,131 follow 129
INSERT INTO follows VALUES ('30', '29', '2022-09-01');
INSERT INTO follows VALUES ('31', '29', '2022-09-01');

INSERT INTO tweets VALUES (12901, '29', '2022-09-07', 'tweet1 of usr129', NULL);
INSERT INTO tweets VALUES (12902, '29', '2022-09-08', 'tweet2 of usr129', NULL);
INSERT INTO tweets VALUES (12903, '29', '2022-09-09', 'tweet3 of usr129', NULL);
INSERT INTO tweets VALUES (12904, '29', '2022-09-10', 'tweet4 of usr129', NULL);
INSERT INTO tweets VALUES (12905, '29', '2022-09-11', 'tweet5 of usr129', NULL);

-- Application 4
INSERT INTO hashtags VALUES ('survivor');
INSERT INTO hashtags VALUES ('dba');

-- Application 5
INSERT INTO users VALUES ('12', 'aaa', '112follow101', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('13', 'aaa', '113follow101', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('14', 'aaa', '114follow101', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('15', 'aaa', '115follow101', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('16', 'aaa', '116follow101', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('17', 'aaa', '117follow101', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('18', 'aaa', '118follow101', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('19', 'aaa', '119follow101', 'usr@email.ca', 'Rome');
INSERT INTO users VALUES ('20', 'aaa', '120follow101', 'usr@email.ca', 'Rome');

INSERT INTO follows VALUES ('12', '1', '2022-09-01');
INSERT INTO follows VALUES ('13', '1', '2022-09-01');
INSERT INTO follows VALUES ('14', '1', '2022-09-01');
INSERT INTO follows VALUES ('15', '1', '2022-09-01');

-- 15 follows 1, 12,13,14
-- 15 is followed by 12, 13, 14
INSERT INTO follows VALUES ('15', '12', '2022-09-01');
INSERT INTO follows VALUES ('15', '13', '2022-09-01');
INSERT INTO follows VALUES ('15', '14', '2022-09-01');

INSERT INTO follows VALUES ('12', '15', '2022-09-01');
INSERT INTO follows VALUES ('13', '15', '2022-09-01');
INSERT INTO follows VALUES ('14', '15', '2022-09-01');

INSERT INTO tweets VALUES (11501, '15', '2022-09-07', 'tweet1 of usr115', NULL);
INSERT INTO tweets VALUES (11502, '15', '2022-09-08', 'tweet2 of usr115', NULL);
INSERT INTO tweets VALUES (11503, '15', '2022-09-09', 'tweet3 of usr115', NULL);
INSERT INTO tweets VALUES (11504, '15', '2022-09-10', 'tweet4 of usr115', NULL);
INSERT INTO tweets VALUES (11505, '15', '2022-09-11', 'tweet5 of usr115', NULL);
