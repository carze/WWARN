DELIMITER //

CREATE PROCEDURE total_genotyped ()
BEGIN
DECLARE select_string varchar(300);
DECLARE from_string varchar(500);
DECLARE groupby_string varchar(300);

SET @query = CONCAT('SELECT s.label, l.site, p.age, m.locus_name, ' ,
                    'm.locus_position, g.value ' ,
                    'FROM study s JOIN location l ON s.id_study = l.fk_study_id ' ,
                    'LEFT JOIN subject p ON p.fk_location_id = l.id_location ' ,
                    'JOIN sample sp ON sp.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g ON g.fk_sample_id = sp.id_sample ' ,
                    'JOIN marker m ON m.id_marker = g.fk_marker_id ' ,
                    'WHERE m.type = "SNP" ' ,
                    'AND g.value NOT IN ("No data", "Fail")');

PREPARE stmt FROM @query;
EXECUTE stmt;
END
//

DELIMITER ;
