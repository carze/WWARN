DELIMITER //

DROP PROCEDURE IF EXISTS quintuple_haplotype_genotype_counts//

CREATE PROCEDURE quintuple_haplotype_genotype_counts (IN locus1_name VARCHAR(64), IN locus1_pos INT(10), 
                                                      IN locus2_name VARCHAR(64), IN locus2_pos INT(10), 
                                                      IN locus3_name VARCHAR(64), IN locus3_pos INT(10), 
                                                      IN locus4_name VARCHAR(64), IN locus4_pos INT(10), 
                                                      IN locus5_name VARCHAR(64), IN locus5_pos INT(10), 
                                                      IN where_clause TEXT)

BEGIN
DECLARE select_string varchar(300);
DECLARE from_string varchar(500);

SET @select_string = CONCAT('SELECT s.wwarn_study_id, s.label, s.investigator, l.country, l.site, p.patient_id, p.age, p.date_of_inclusion, ' , 
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
END
//

DELIMITER ;
