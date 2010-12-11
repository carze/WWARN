SELECT s.label, s.investigator, l.country, l.site, p.age, CONCAT(m.locus_name, '_', m.locus_position, '_', g.value) AS "marker"
FROM study s JOIN location l ON s.id_study = l.fk_study_id
LEFT JOIN subject p ON p.fk_location_id = l.id_location
JOIN sample sp ON sp.fk_subject_id = p.id_subject
JOIN genotype g ON g.fk_sample_id = sp.id_sample
JOIN marker m ON m.id_marker = g.fk_marker_id
WHERE m.type = "SNP"
AND g.value NOT IN ("No data", "Fail")

UNION ALL

SELECT s.label, s.investigator, l.country, l.site, p.age, CONCAT(m1.locus_name, "_", m1.locus_position, "_", g1.value, ' +', m2.locus_name, "_", m2.locus_position, "_", g2.value) AS "marker"
FROM study s JOIN location l ON s.id_study = l.fk_study_id
JOIN subject p ON p.fk_location_id = l.id_location AND p.age IS NOT NULL
JOIN sample sp1 ON sp1.fk_subject_id = p.id_subject
JOIN genotype g1 ON g1.fk_sample_id = sp1.id_sample 
JOIN marker m1 ON m1.id_marker = g1.fk_marker_id
JOIN sample sp2 ON sp2.fk_subject_id = p.id_subject
JOIN genotype g2 ON g2.fk_sample_id = sp2.id_sample
JOIN marker m2 ON m2.id_marker = g2.fk_marker_id
WHERE m1.locus_name = 'pfdhps' AND m1.locus_position = '437' AND g1.value = 'G'
AND m2.locus_name = 'pfdhps' AND m2.locus_position = '540' AND g2.value = 'E'
AND m1.type = "SNP" AND m2.type = 'SNP'
GROUP BY s.label, l.site, p.age

UNION ALL

SELECT s.label, s.investigator, l.country, l.site, p.age, CONCAT(m1.locus_name, "_", m1.locus_position, "_", g1.value, ' +', m2.locus_name, "_", m2.locus_position, "_", g2.value) AS "marker"
FROM study s JOIN location l ON s.id_study = l.fk_study_id
JOIN subject p ON p.fk_location_id = l.id_location AND p.age IS NOT NULL
JOIN sample sp1 ON sp1.fk_subject_id = p.id_subject
JOIN genotype g1 ON g1.fk_sample_id = sp1.id_sample 
JOIN marker m1 ON m1.id_marker = g1.fk_marker_id
JOIN sample sp2 ON sp2.fk_subject_id = p.id_subject
JOIN genotype g2 ON g2.fk_sample_id = sp2.id_sample
JOIN marker m2 ON m2.id_marker = g2.fk_marker_id
WHERE m1.locus_name = 'pfdhps' AND m1.locus_position = '437' AND g1.value = 'G'
AND m2.locus_name = 'pfdhps' AND m2.locus_position = '540' AND g2.value = 'K/E'
AND m1.type = "SNP" AND m2.type = 'SNP'
GROUP BY s.label, l.site, p.age

UNION ALL

SELECT s.label, s.investigator, l.country, l.site, p.age, CONCAT(m1.locus_name, "_", m1.locus_position, "_", g1.value, ' +', m2.locus_name, "_", m2.locus_position, "_", g2.value) AS "marker"
FROM study s JOIN location l ON s.id_study = l.fk_study_id
JOIN subject p ON p.fk_location_id = l.id_location AND p.age IS NOT NULL
JOIN sample sp1 ON sp1.fk_subject_id = p.id_subject
JOIN genotype g1 ON g1.fk_sample_id = sp1.id_sample 
JOIN marker m1 ON m1.id_marker = g1.fk_marker_id
JOIN sample sp2 ON sp2.fk_subject_id = p.id_subject
JOIN genotype g2 ON g2.fk_sample_id = sp2.id_sample
JOIN marker m2 ON m2.id_marker = g2.fk_marker_id
WHERE m1.locus_name = 'pfdhps' AND m1.locus_position = '540' AND g1.value = 'E'
AND m2.locus_name = 'pfdhps' AND m2.locus_position = '537' AND g2.value = 'A/G'
AND m1.type = "SNP" AND m2.type = 'SNP'
GROUP BY s.label, l.site, p.age

UNION ALL

SELECT s.label, s.investigator, l.country, l.site, p.age, CONCAT(m1.locus_name, "_", m1.locus_position, "_", g1.value, " + ", m2.locus_name, "_", m2.locus_position, "_", g2.value, " +  ", m3.locus_name, "_", m3.locus_position, "_", g3.value) AS "marker"
FROM study s JOIN location l ON s.id_study = l.fk_study_id
JOIN subject p ON p.fk_location_id = l.id_location AND p.age IS NOT NULL
JOIN sample sp1 ON sp1.fk_subject_id = p.id_subject
JOIN genotype g1 ON g1.fk_sample_id = sp1.id_sample
JOIN marker m1 ON m1.id_marker = g1.fk_marker_id
JOIN sample sp2 ON sp2.fk_subject_id = p.id_subject
JOIN genotype g2 ON g2.fk_sample_id = sp2.id_sample
JOIN marker m2 ON m2.id_marker = g2.fk_marker_id
JOIN sample sp3 ON sp3.fk_subject_id = p.id_subject
JOIN genotype g3 ON g3.fk_sample_id = sp3.id_sample
JOIN marker m3 ON m3.id_marker = g3.fk_marker_id
WHERE m1.locus_name = "pfdhfr" AND m1.locus_position = "108" AND g1.value = "N" 
AND m2.locus_name = "pfdhfr" AND m2.locus_position = "51" AND g2.value = "I"
AND m3.locus_name = "pfdhfr" AND m3.locus_position = "59" AND g3.value = "R"
AND m1.type = "SNP" AND m2.type = "SNP" AND m3.type = "SNP"
AND g1.value NOT IN ("No data", "Fail") AND g2.value NOT IN ("No data", "Fail") AND g3.value NOT IN ("No data", "Fail")
GROUP BY s.label, l.site, p.age

UNION ALL

SELECT s.label, s.investigator, l.country, l.site, p.age, CONCAT(m1.locus_name, "_", m1.locus_position, "_", g1.value, " + ", m2.locus_name, "_", m2.locus_position, "_", g2.value, " +  ", m3.locus_name, "_", m3.locus_position, "_", g3.value) AS "marker"
FROM study s JOIN location l ON s.id_study = l.fk_study_id
JOIN subject p ON p.fk_location_id = l.id_location AND p.age IS NOT NULL
JOIN sample sp1 ON sp1.fk_subject_id = p.id_subject
JOIN genotype g1 ON g1.fk_sample_id = sp1.id_sample
JOIN marker m1 ON m1.id_marker = g1.fk_marker_id
JOIN sample sp2 ON sp2.fk_subject_id = p.id_subject
JOIN genotype g2 ON g2.fk_sample_id = sp2.id_sample
JOIN marker m2 ON m2.id_marker = g2.fk_marker_id
JOIN sample sp3 ON sp3.fk_subject_id = p.id_subject
JOIN genotype g3 ON g3.fk_sample_id = sp3.id_sample
JOIN marker m3 ON m3.id_marker = g3.fk_marker_id
WHERE m1.locus_name = "pfdhfr" AND m1.locus_position = "108" AND g1.value = "N" 
AND m2.locus_name = "pfdhfr" AND m2.locus_position = "51" AND g2.value = "N/I"
AND m3.locus_name = "pfdhfr" AND m3.locus_position = "59" AND g3.value = "R"
AND m1.type = "SNP" AND m2.type = "SNP" AND m3.type = "SNP"
AND g1.value NOT IN ("No data", "Fail") AND g2.value NOT IN ("No data", "Fail") AND g3.value NOT IN ("No data", "Fail")
GROUP BY s.label, l.site, p.age

UNION ALL

SELECT s.label, s.investigator, l.country, l.site, p.age, CONCAT(m1.locus_name, "_", m1.locus_position, "_", g1.value, " + ", m2.locus_name, "_", m2.locus_position, "_", g2.value, " +  ", m3.locus_name, "_", m3.locus_position, "_", g3.value) AS "marker"
FROM study s JOIN location l ON s.id_study = l.fk_study_id
JOIN subject p ON p.fk_location_id = l.id_location AND p.age IS NOT NULL
JOIN sample sp1 ON sp1.fk_subject_id = p.id_subject
JOIN genotype g1 ON g1.fk_sample_id = sp1.id_sample
JOIN marker m1 ON m1.id_marker = g1.fk_marker_id
JOIN sample sp2 ON sp2.fk_subject_id = p.id_subject
JOIN genotype g2 ON g2.fk_sample_id = sp2.id_sample
JOIN marker m2 ON m2.id_marker = g2.fk_marker_id
JOIN sample sp3 ON sp3.fk_subject_id = p.id_subject
JOIN genotype g3 ON g3.fk_sample_id = sp3.id_sample
JOIN marker m3 ON m3.id_marker = g3.fk_marker_id
WHERE m1.locus_name = "pfdhfr" AND m1.locus_position = "108" AND g1.value = "S/N" 
AND m2.locus_name = "pfdhfr" AND m2.locus_position = "51" AND g2.value = "I"
AND m3.locus_name = "pfdhfr" AND m3.locus_position = "59" AND g3.value = "R"
AND m1.type = "SNP" AND m2.type = "SNP" AND m3.type = "SNP"
AND g1.value NOT IN ("No data", "Fail") AND g2.value NOT IN ("No data", "Fail") AND g3.value NOT IN ("No data", "Fail")
GROUP BY s.label, l.site, p.age

UNION ALL

SELECT s.label, s.investigator, l.country, l.site, p.age, CONCAT(m1.locus_name, "_", m1.locus_position, "_", g1.value, " + ", m2.locus_name, "_", m2.locus_position, "_", g2.value, " +  ", m3.locus_name, "_", m3.locus_position, "_", g3.value) AS "marker"
FROM study s JOIN location l ON s.id_study = l.fk_study_id
JOIN subject p ON p.fk_location_id = l.id_location AND p.age IS NOT NULL
JOIN sample sp1 ON sp1.fk_subject_id = p.id_subject
JOIN genotype g1 ON g1.fk_sample_id = sp1.id_sample
JOIN marker m1 ON m1.id_marker = g1.fk_marker_id
JOIN sample sp2 ON sp2.fk_subject_id = p.id_subject
JOIN genotype g2 ON g2.fk_sample_id = sp2.id_sample
JOIN marker m2 ON m2.id_marker = g2.fk_marker_id
JOIN sample sp3 ON sp3.fk_subject_id = p.id_subject
JOIN genotype g3 ON g3.fk_sample_id = sp3.id_sample
JOIN marker m3 ON m3.id_marker = g3.fk_marker_id
WHERE m1.locus_name = "pfdhfr" AND m1.locus_position = "108" AND g1.value = "N" 
AND m2.locus_name = "pfdhfr" AND m2.locus_position = "51" AND g2.value = "I"
AND m3.locus_name = "pfdhfr" AND m3.locus_position = "59" AND g3.value = "C/R"
AND m1.type = "SNP" AND m2.type = "SNP" AND m3.type = "SNP"
AND g1.value NOT IN ("No data", "Fail") AND g2.value NOT IN ("No data", "Fail") AND g3.value NOT IN ("No data", "Fail")
GROUP BY s.label, l.site, p.age

UNION ALL

SELECT s.label, s.investigator, l.country, l.site, p.age, CONCAT(m1.locus_name, "_", m1.locus_position, "_", g1.value, " + ", m2.locus_name, "_", m2.locus_position, "_", g2.value," +  ", m3.locus_name, "_", m3.locus_position, "_", g3.value, " +  ", m4.locus_name, "_", m4.locus_position, "_", g4.value, " +  ", m5.locus_name, "_", m5.locus_position, "_", g5.value) AS "marker"
FROM study s JOIN location l ON s.id_study = l.fk_study_id
JOIN subject p ON p.fk_location_id = l.id_location AND p.age IS NOT NULL
JOIN sample sp1 ON sp1.fk_subject_id = p.id_subject
JOIN genotype g1 ON g1.fk_sample_id = sp1.id_sample
JOIN marker m1 ON m1.id_marker = g1.fk_marker_id
JOIN sample sp2 ON sp2.fk_subject_id = p.id_subject
JOIN genotype g2 ON g2.fk_sample_id = sp2.id_sample
JOIN marker m2 ON m2.id_marker = g2.fk_marker_id
JOIN sample sp3 ON sp3.fk_subject_id = p.id_subject
JOIN genotype g3 ON g3.fk_sample_id = sp3.id_sample
JOIN marker m3 ON m3.id_marker = g3.fk_marker_id
JOIN sample sp4 ON sp4.fk_subject_id = p.id_subject
JOIN genotype g4 ON g4.fk_sample_id = sp4.id_sample
JOIN marker m4 ON m4.id_marker = g4.fk_marker_id
JOIN sample sp5 ON sp5.fk_subject_id = p.id_subject
JOIN genotype g5 ON g5.fk_sample_id = sp5.id_sample
JOIN marker m5 ON m5.id_marker = g5.fk_marker_id
WHERE m1.locus_name = "pfdhfr" AND m1.locus_position = "108" AND g1.value = "N" 
AND m2.locus_name = "pfdhfr" AND m2.locus_position = "51" AND g2.value = "I"
AND m3.locus_name = "pfdhfr" AND m3.locus_position = "59" AND g3.value = "R"
AND m4.locus_name = "pfdhps" AND m4.locus_position = "437" AND g4.value = "G"
AND m5.locus_name = "pfdhps" AND m5.locus_position = "540" AND g5.value = "E"
AND m1.type = "SNP" AND m2.type = "SNP" AND m3.type = "SNP" AND m4.type = "SNP" AND m5.type = "SNP"
AND g1.value NOT IN ("No data", "Fail") AND g2.value NOT IN ("No data", "Fail")
AND g3.value NOT IN ("No data", "Fail") AND g4.value NOT IN ("No data", "Fail")
AND g5.value NOT IN ("No data", "Fail")
GROUP BY s.label, l.site, p.age
