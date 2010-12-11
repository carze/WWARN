DELIMITER //

CREATE PROCEDURE single_marker_sample_size (IN group_by SET('age', 'study'))
BEGIN
DECLARE select_string varchar(300);
DECLARE from_string varchar(500);
DECLARE groupby_string varchar(300);

SET @select_string = CONCAT('SELECT s.label, s.investigator, l.country, l.site, ' ,
                            'CONCAT(m.locus_name, "_", m.locus_position, "_", g.value) AS "marker", ');

SET @from_string = CONCAT('FROM study s JOIN location l ON s.id_study = l.fk_study_id ' ,
                    'LEFT JOIN subject p ON p.fk_location_id = l.id_location ' ,
                    'JOIN sample sp ON sp.fk_subject_id = p.id_subject ' ,
                    'JOIN genotype g ON g.fk_sample_id = sp.id_sample ' ,
                    'JOIN marker m ON m.id_marker = g.fk_marker_id ' ,
                    'WHERE m.type = "SNP" ' ,
                    'AND g.value NOT IN ("No data", "Fail") ' ,
                    'AND g.mutant_status IN ("Mutant", "Mixed") ');

IF group_by = "age" THEN
    SET @select_string = CONCAT(@select_string , 'p.age ');
    SET @groupby_string = CONCAT('GROUP BY s.label, l.site, m.locus_name, m.locus_position, g.value, p.patient_id');
ELSEIF group_by = "study" THEN
    SET @groupby_string = CONCAT('GROUP BY s.label, l.site,  m.locus_name, m.locus_position, g.value');
    SET @select_string = CONCAT(@select_string, 'COUNT(g.id_genotype) AS "sample_size" ');
END IF; 

SET @query = CONCAT(@select_string, @from_string, @groupby_string);

PREPARE stmt FROM @query;
EXECUTE stmt;
END
//

DELIMITER ;
