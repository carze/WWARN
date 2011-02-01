SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL';

CREATE SCHEMA IF NOT EXISTS `WWARNv2` DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci ;

-- -----------------------------------------------------
-- Table `WWARNv2`.`study`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `WWARNv2`.`study` (
  `id_study` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `wwarn_study_id` VARCHAR(45) NULL ,
  `investigator` VARCHAR(45) NOT NULL ,
  `label` VARCHAR(45) NOT NULL ,
  `group` VARCHAR(45) NOT NULL ,
  PRIMARY KEY (`id_study`) ,
  UNIQUE INDEX `label_UNIQUE` (`label` ASC) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `WWARNv2`.`location`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `WWARNv2`.`location` (
  `id_location` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `fk_study_id` INT UNSIGNED NOT NULL ,
  `country` VARCHAR(45) NOT NULL ,
  `site` VARCHAR(45) NULL ,
  PRIMARY KEY (`id_location`) ,
  INDEX `fk_study_id_loc` (`fk_study_id` ASC) ,
  CONSTRAINT `fk_study_id_loc`
    FOREIGN KEY (`fk_study_id` )
    REFERENCES `WWARNv2`.`study` (`id_study` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `WWARNv2`.`subject`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `WWARNv2`.`subject` (
  `id_subject` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `fk_study_id` INT UNSIGNED NOT NULL ,
  `fk_location_id` INT UNSIGNED NOT NULL ,
  `patient_id` VARCHAR(45) NOT NULL ,
  `age` DECIMAL(13,10) NULL DEFAULT NULL ,
  `date_of_inclusion` DATE NULL DEFAULT NULL ,
  PRIMARY KEY (`id_subject`) ,
  INDEX `fk_study_id_study` (`fk_study_id` ASC) ,
  INDEX `fk_location_id_location` (`fk_location_id` ASC) ,
  CONSTRAINT `fk_study_id_study`
    FOREIGN KEY (`fk_study_id` )
    REFERENCES `WWARNv2`.`study` (`id_study` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_location_id_location`
    FOREIGN KEY (`fk_location_id` )
    REFERENCES `WWARNv2`.`location` (`id_location` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `WWARNv2`.`sample`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `WWARNv2`.`sample` (
  `id_sample` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `fk_subject_id` INT UNSIGNED NOT NULL ,
  `collection_date` DATE NULL DEFAULT NULL ,
  PRIMARY KEY (`id_sample`) ,
  INDEX `fk_subject_id` (`fk_subject_id` ASC) ,
  CONSTRAINT `fk_subject_id`
    FOREIGN KEY (`fk_subject_id` )
    REFERENCES `WWARNv2`.`subject` (`id_subject` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `WWARNv2`.`marker`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `WWARNv2`.`marker` (
  `id_marker` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `locus_name` VARCHAR(45) NOT NULL ,
  `locus_position` INT NOT NULL ,
  `type` SET('SNP','Copy Number','Fragment') NOT NULL ,
  PRIMARY KEY (`id_marker`) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `WWARNv2`.`genotype`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `WWARNv2`.`genotype` (
  `id_genotype` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `fk_sample_id` INT UNSIGNED NOT NULL ,
  `fk_marker_id` INT UNSIGNED NOT NULL ,
  `value` VARCHAR(45) NOT NULL ,
  `mutant_status` SET('Wild','Mutant','Mixed','No data') NULL ,
  `molecule_type` SET('Amino Acid','Nucleotide') NULL ,
  PRIMARY KEY (`id_genotype`) ,
  INDEX `fk_sample_id` (`fk_sample_id` ASC) ,
  INDEX `fk_marker_id` (`fk_marker_id` ASC) ,
  CONSTRAINT `fk_sample_id`
    FOREIGN KEY (`fk_sample_id` )
    REFERENCES `WWARNv2`.`sample` (`id_sample` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_marker_id`
    FOREIGN KEY (`fk_marker_id` )
    REFERENCES `WWARNv2`.`marker` (`id_marker` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;



SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
