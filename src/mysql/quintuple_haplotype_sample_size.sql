DELIMITER //

CREATE PROCEDURE quintuple_haplotype_sample_size (IN locus1_name VARCHAR(64), IN locus1_pos INT(10), IN locus1_genotype VARCHAR(64),
                                                  IN locus2_name VARCHAR(64), IN locus2_pos INT(10), IN locus2_genotype VARCHAR(64),
                                                  IN locus3_name VARCHAR(64), IN locus3_pos INT(10), IN locus3_genotype VARCHAR(64),
                                                  IN locus4_name VARCHAR(64), IN locus4_pos INT(10), IN locus4_genotype VARCHAR(64),
                                                  IN locus5_name VARCHAR(64), IN locus5_pos INT(10), IN locus5_genotype VARCHAR(64),
                                                  IN group_by SET('age', 'study'))
BEGIN
DECLARE select_string varchar(300);
DECLARE from_string varchar(500);
DECLARE groupby_string varchar(300);

SET @select_string = CONCAT('SELECT s.label, s.investigator, l.country, l.site, ' ,
                            'CONCAT(m1.locus_name, "_", m1.locus_position, "_", g1.value, ' , 
                            '" + ", m2.locus_name, "_", m2.locus_position, "_", g2.value, ' ,
                            '" +  ", m3.locus_name, "_", m3.locus_position, "_", g3.value, ' ,
                            '" +  ", m4.locus_name, "_", m4.locus_position, "_", g4.value, ' ,
                            '" +  ", m5.locus_name, "_", m5.locus_position, "_", g5.value) AS "marker", ');

SET @from_string = CONCAT('FROM study s JOIN location l ON s.id_study = l.fk_study_id ' ,
                    'JOIN subject p ON p.fk_location_id = l.id_location AND p.age IS NOT NULL ' ,
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
                    'AND g1.value = "' , locus1_genotype , '" AND m2.locus_name = "' , locus2_name , '" ' ,
                    'AND m2.locus_position = "' , locus2_pos , '" AND g2.value = "' , locus2_genotype , '" ' ,
                    'AND m3.locus_name = "' , locus3_name , '" AND m3.locus_position = "' , locus3_pos , '" ' ,
                    'AND g3.value = "' , locus3_genotype , '" ' , 
                    'AND m4.locus_name = "' , locus4_name , '" AND m4.locus_position = "' , locus4_pos , '" ' ,
                    'AND g4.value = "' , locus4_genotype , '" ' , 
                    'AND m5.locus_name = "' , locus5_name , '" AND m5.locus_position = "' , locus5_pos , '" ' ,
                    'AND g5.value = "' , locus5_genotype , '" ' , 
                    'AND m1.type = "SNP" AND m2.type = "SNP" AND m3.type = "SNP" AND m4.type = "SNP" AND m5.type = "SNP"' ,
                    'AND g1.value NOT IN ("No data", "Fail") AND g2.value NOT IN ("No data", "Fail") ' ,
                    'AND g3.value NOT IN ("No data", "Fail") AND g4.value NOT IN ("No data", "Fail") ' ,
                    'AND g5.value NOT IN ("No data", "Fail") ');

IF group_by = "age" THEN
    SET @select_string = CONCAT(@select_string , 'p.age ');
    SET @groupby_string = CONCAT('GROUP BY s.label, l.site, p.age');
ELSEIF group_by = "study" THEN
    SET @groupby_string = CONCAT('GROUP BY s.label, l.site');
    SET @select_string = CONCAT(@select_string, 'COUNT(p.patient_id) AS "sample_size" ');
END IF;

SET @query = CONCAT(@select_string, @from_string, @groupby_string);

PREPARE stmt FROM @query;
EXECUTE stmt;
END
//

DELIMITER ;
