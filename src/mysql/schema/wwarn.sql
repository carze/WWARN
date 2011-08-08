-- MySQL dump 10.11
-- ------------------------------------------------------
-- Server version	5.0.77

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `genotype`
--

DROP TABLE IF EXISTS `genotype`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `genotype` (
  `id_genotype` int(10) unsigned NOT NULL auto_increment,
  `fk_sample_id` int(10) unsigned NOT NULL,
  `fk_marker_id` int(10) unsigned NOT NULL,
  `value` varchar(45) NOT NULL,
  `mutant_status` set('Wild','Mutant','Mixed','No data') default NULL,
  `molecule_type` set('Amino Acid','Nucleotide') default NULL,
  PRIMARY KEY  (`id_genotype`),
  KEY `fk_sample_id` (`fk_sample_id`),
  KEY `fk_marker_id` (`fk_marker_id`),
  CONSTRAINT `fk_sample_id` FOREIGN KEY (`fk_sample_id`) REFERENCES `sample` (`id_sample`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_marker_id` FOREIGN KEY (`fk_marker_id`) REFERENCES `marker` (`id_marker`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `genotype`
--

LOCK TABLES `genotype` WRITE;
/*!40000 ALTER TABLE `genotype` DISABLE KEYS */;
/*!40000 ALTER TABLE `genotype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `location`
--

DROP TABLE IF EXISTS `location`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `location` (
  `id_location` int(10) unsigned NOT NULL auto_increment,
  `fk_study_id` int(10) unsigned NOT NULL,
  `country` varchar(45) NOT NULL,
  `site` varchar(45) default NULL,
  PRIMARY KEY  (`id_location`),
  KEY `fk_study_id_loc` (`fk_study_id`),
  CONSTRAINT `fk_study_id_loc` FOREIGN KEY (`fk_study_id`) REFERENCES `study` (`id_study`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `location`
--

LOCK TABLES `location` WRITE;
/*!40000 ALTER TABLE `location` DISABLE KEYS */;
/*!40000 ALTER TABLE `location` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `marker`
--

DROP TABLE IF EXISTS `marker`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `marker` (
  `id_marker` int(10) unsigned NOT NULL auto_increment,
  `locus_name` varchar(45) NOT NULL,
  `locus_position` int(11) NOT NULL,
  `type` set('SNP','Copy Number','Fragment') NOT NULL,
  PRIMARY KEY  (`id_marker`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `marker`
--

LOCK TABLES `marker` WRITE;
/*!40000 ALTER TABLE `marker` DISABLE KEYS */;
/*!40000 ALTER TABLE `marker` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sample`
--

DROP TABLE IF EXISTS `sample`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `sample` (
  `id_sample` int(10) unsigned NOT NULL auto_increment,
  `fk_subject_id` int(10) unsigned NOT NULL,
  `collection_date` date default NULL,
  PRIMARY KEY  (`id_sample`),
  KEY `fk_subject_id` (`fk_subject_id`),
  CONSTRAINT `fk_subject_id` FOREIGN KEY (`fk_subject_id`) REFERENCES `subject` (`id_subject`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `sample`
--

LOCK TABLES `sample` WRITE;
/*!40000 ALTER TABLE `sample` DISABLE KEYS */;
/*!40000 ALTER TABLE `sample` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `study`
--

DROP TABLE IF EXISTS `study`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `study` (
  `id_study` int(10) unsigned NOT NULL auto_increment,
  `wwarn_study_id` varchar(45) default NULL,
  `investigator` varchar(45) NOT NULL,
  `label` varchar(45) NOT NULL,
  `group` varchar(45) NOT NULL,
  PRIMARY KEY  (`id_study`),
  UNIQUE KEY `label_UNIQUE` (`label`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `study`
--

LOCK TABLES `study` WRITE;
/*!40000 ALTER TABLE `study` DISABLE KEYS */;
/*!40000 ALTER TABLE `study` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `subject`
--

DROP TABLE IF EXISTS `subject`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `subject` (
  `id_subject` int(10) unsigned NOT NULL auto_increment,
  `fk_study_id` int(10) unsigned NOT NULL,
  `fk_location_id` int(10) unsigned NOT NULL,
  `patient_id` varchar(45) NOT NULL,
  `age` decimal(13,10) default NULL,
  `date_of_inclusion` date default NULL,
  PRIMARY KEY  (`id_subject`),
  KEY `fk_study_id_study` (`fk_study_id`),
  KEY `fk_location_id_location` (`fk_location_id`),
  CONSTRAINT `fk_study_id_study` FOREIGN KEY (`fk_study_id`) REFERENCES `study` (`id_study`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_location_id_location` FOREIGN KEY (`fk_location_id`) REFERENCES `location` (`id_location`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `subject`
--

LOCK TABLES `subject` WRITE;
/*!40000 ALTER TABLE `subject` DISABLE KEYS */;
/*!40000 ALTER TABLE `subject` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'wwarn'
--
DELIMITER ;;
/*!50003 DROP PROCEDURE IF EXISTS `double_haplotype_genotype_counts` */;;
/*!50003 SET SESSION SQL_MODE=""*/;;
/*!50003 CREATE*/ /*!50020 DEFINER=`carze`@`%.igs.umaryland.edu`*/ /*!50003 PROCEDURE `double_haplotype_genotype_counts`(IN locus1_name VARCHAR(64), IN locus1_pos INT(10),
                                                   IN locus2_name VARCHAR(64), IN locus2_pos INT(10),
                                                   IN where_clause TEXT)
BEGIN
DECLARE select_string varchar(300);
DECLARE from_string varchar(500);

SET @select_string = CONCAT('SELECT s.wwarn_study_id, s.label, s.investigator, l.country, l.site, p.patient_id, p.age, ' ,
                            'CONCAT(m1.locus_name, "_", m1.locus_position, "_", m1.type, ' , 
                            '" + ", m2.locus_name, "_", m2.locus_position, "_", m2.type) AS "marker", ' ,
                            'CONCAT(g1.value, " + ", g2.value) AS "genotype" ');

SET @from_string = CONCAT('FROM study s JOIN location l ON s.id_study = l.fk_study_id ' ,
                    'JOIN subject p ON p.fk_location_id = l.id_location ' ,
                    'JOIN sample sp1 ON sp1.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g1 ON g1.fk_sample_id = sp1.id_sample ' ,
                    'JOIN marker m1 ON m1.id_marker = g1.fk_marker_id ' ,
                    'JOIN sample sp2 ON sp2.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g2 ON g2.fk_sample_id = sp2.id_sample ' ,
                    'JOIN marker m2 ON m2.id_marker = g2.fk_marker_id ' ,
                    'WHERE m1.locus_name = "' , locus1_name , '" AND m1.locus_position = "' , locus1_pos , '" ' ,
                    'AND m2.locus_name = "' , locus2_name , '" AND m2.locus_position = "' , locus2_pos , '" ',
                    'AND g1.value NOT IN ("Genotyping Failure", "Not Genotyped") ',
                    'AND g2.value NOT IN ("Genotyping Failure", "Not Genotyped") ');

SET @query = CONCAT(@select_string, @from_string, where_clause);

PREPARE stmt FROM @query;
EXECUTE stmt;
END */;;
/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE*/;;
/*!50003 DROP PROCEDURE IF EXISTS `quintuple_haplotype_genotype_counts` */;;
/*!50003 SET SESSION SQL_MODE=""*/;;
/*!50003 CREATE*/ /*!50020 DEFINER=`carze`@`%.igs.umaryland.edu`*/ /*!50003 PROCEDURE `quintuple_haplotype_genotype_counts`(IN locus1_name VARCHAR(64), IN locus1_pos INT(10), 
                                                      IN locus2_name VARCHAR(64), IN locus2_pos INT(10), 
                                                      IN locus3_name VARCHAR(64), IN locus3_pos INT(10), 
                                                      IN locus4_name VARCHAR(64), IN locus4_pos INT(10), 
                                                      IN locus5_name VARCHAR(64), IN locus5_pos INT(10), 
                                                      IN where_clause TEXT)
BEGIN
DECLARE select_string varchar(300);
DECLARE from_string varchar(500);

SET @select_string = CONCAT('SELECT s.wwarn_study_id, s.label, s.investigator, l.country, l.site, p.patient_id, p.age, ' , 
                            'CONCAT(m1.locus_name, "_", m1.locus_position, "_", m1.type, ' , 
                            '" + ", m2.locus_name, "_", m2.locus_position, "_", m2.type, ' ,
                            '" + ", m3.locus_name, "_", m3.locus_position, "_", m3.type, ' ,
                            '" + ", m4.locus_name, "_", m4.locus_position, "_", m4.type, ' ,
                            '" + ", m5.locus_name, "_", m5.locus_position, "_", m5.type) AS "marker", ' ,
                            'CONCAT(g1.value, " + ", g2.value, " + ", g3.value, " + ", ' ,
                            'g4.value, " + ", g5.value) AS "genotype" ');

SET @from_string = CONCAT('FROM study s JOIN location l ON s.id_study = l.fk_study_id ' ,
                    'JOIN subject p ON p.fk_location_id = l.id_location ' ,
                    'JOIN sample sp1 ON sp1.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g1 ON g1.fk_sample_id = sp1.id_sample ' ,
                    'JOIN marker m1 ON m1.id_marker = g1.fk_marker_id ' ,
                    'JOIN sample sp2 ON sp2.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g2 ON g2.fk_sample_id = sp2.id_sample ' ,
                    'JOIN marker m2 ON m2.id_marker = g2.fk_marker_id ' ,
                    'JOIN sample sp3 ON sp3.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g3 ON g3.fk_sample_id = sp3.id_sample ' ,
                    'JOIN marker m3 ON m3.id_marker = g3.fk_marker_id ' ,
                    'JOIN sample sp4 ON sp4.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g4 ON g4.fk_sample_id = sp4.id_sample ' ,
                    'JOIN marker m4 ON m4.id_marker = g4.fk_marker_id ' ,
                    'JOIN sample sp5 ON sp5.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g5 ON g5.fk_sample_id = sp5.id_sample ' ,
                    'JOIN marker m5 ON m5.id_marker = g5.fk_marker_id ' ,
                    'WHERE m1.locus_name = "' , locus1_name , '" AND m1.locus_position = "' , locus1_pos , '" ' ,
                    'AND m2.locus_name = "' , locus2_name , '" AND m2.locus_position = "' , locus2_pos , '" ' ,
                    'AND m3.locus_name = "' , locus3_name , '" AND m3.locus_position = "' , locus3_pos , '" ' ,
                    'AND m4.locus_name = "' , locus4_name , '" AND m4.locus_position = "' , locus4_pos , '" ' ,
                    'AND m5.locus_name = "' , locus5_name , '" AND m5.locus_position = "' , locus5_pos , '" ' ,
                    'AND g1.value NOT IN ("Not Genotyped", "Genotyping Failure") AND g2.value NOT IN ("Not Genotyped", "Genotyping Failure") ' ,
                    'AND g3.value NOT IN ("Not Genotyped", "Genotyping Failure") AND g4.value NOT IN ("Not Genotyped", "Genotyping Failure") ' ,
                    'AND g5.value NOT IN ("Not Genotyped", "Genotyping Failure") ');

SET @query = CONCAT(@select_string, @from_string, where_clause);

PREPARE stmt FROM @query;
EXECUTE stmt;
END */;;
/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE*/;;
/*!50003 DROP PROCEDURE IF EXISTS `triple_haplotype_genotype_counts` */;;
/*!50003 SET SESSION SQL_MODE=""*/;;
/*!50003 CREATE*/ /*!50020 DEFINER=`carze`@`%.igs.umaryland.edu`*/ /*!50003 PROCEDURE `triple_haplotype_genotype_counts`(IN locus1_name VARCHAR(64), IN locus1_pos INT(10),
                                                   IN locus2_name VARCHAR(64), IN locus2_pos INT(10),
                                                   IN locus3_name VARCHAR(64), IN locus3_pos INT(10),
                                                   IN where_clause TEXT)
BEGIN
DECLARE select_string varchar(300);
DECLARE from_string varchar(500);

SET @select_string = CONCAT('SELECT s.wwarn_study_id, s.label, s.investigator, l.country, l.site, p.patient_id, p.age, ' ,
                            'CONCAT(m1.locus_name, "_", m1.locus_position, "_", m1.type, ' , 
                            '" + ", m2.locus_name, "_", m2.locus_position, "_", m2.type, ' ,
                            '" + ", m3.locus_name, "_", m3.locus_position, "_", m3.type) AS "marker", ' ,
                            'CONCAT(g1.value, " + ", g2.value, " + ", g3.value) AS "genotype" ');


SET @from_string = CONCAT('FROM study s JOIN location l ON s.id_study = l.fk_study_id ' ,
                    'JOIN subject p ON p.fk_location_id = l.id_location ' ,
                    'JOIN sample sp1 ON sp1.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g1 ON g1.fk_sample_id = sp1.id_sample ' ,
                    'JOIN marker m1 ON m1.id_marker = g1.fk_marker_id ' ,
                    'JOIN sample sp2 ON sp2.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g2 ON g2.fk_sample_id = sp2.id_sample ' ,
                    'JOIN marker m2 ON m2.id_marker = g2.fk_marker_id ' ,
                    'JOIN sample sp3 ON sp3.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g3 ON g3.fk_sample_id = sp3.id_sample ' ,
                    'JOIN marker m3 ON m3.id_marker = g3.fk_marker_id ' ,
                    'WHERE m1.locus_name = "' , locus1_name , '" AND m1.locus_position = "' , locus1_pos , '" ' ,
                    'AND m2.locus_name = "' , locus2_name , '" AND m2.locus_position = "' , locus2_pos , '" ' ,
                    'AND m3.locus_name = "' , locus3_name , '" AND m3.locus_position = "' , locus3_pos , '" ' ,
                    'AND g1.value NOT IN ("Genotyping failure", "Not genotyped") ' ,
                    'AND g2.value NOT IN ("Genotyping failure", "Not genotyped") ',
                    'AND g3.value NOT IN ("Genotyping failure", "Not genotyped") ');

SET @query = CONCAT(@select_string, @from_string, where_clause);

PREPARE stmt FROM @query;
EXECUTE stmt;

END */;;
/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE*/;;
DELIMITER ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2011-04-28 15:03:09
