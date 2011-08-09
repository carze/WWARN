DELIMITER //

DROP PROCEDURE IF EXISTS double_haplotype_genotype_counts//

CREATE PROCEDURE double_haplotype_genotype_counts (IN locus1_name VARCHAR(64), IN locus1_pos INT(10),
                                                   IN locus2_name VARCHAR(64), IN locus2_pos INT(10),
                                                   IN where_clause TEXT)

BEGIN
DECLARE select_string varchar(300);
DECLARE from_string varchar(500);

SET @select_string = CONCAT('SELECT s.wwarn_study_id, s.label, s.investigator, l.country, l.site, p.patient_id, p.age, p.date_of_inclusion, ' ,
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
END
//

DELIMITER ;
