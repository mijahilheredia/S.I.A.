-- MySQL Script generated by MySQL Workbench
-- Thu Nov 25 11:21:09 2021
-- Model: New Model    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema sia
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `sia` ;

-- -----------------------------------------------------
-- Schema sia
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `sia` DEFAULT CHARACTER SET utf8 ;
USE `sia` ;

-- -----------------------------------------------------
-- Table `sia`.`piso`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sia`.`piso` (
  `nro_piso` INT NOT NULL AUTO_INCREMENT,
  `decripcion` VARCHAR(80) NOT NULL,
  PRIMARY KEY (`nro_piso`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `sia`.`apartamento`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sia`.`apartamento` (
  `id_apartamento` INT NOT NULL,
  `propietario` VARCHAR(80) NOT NULL,
  `nro_piso` INT NOT NULL,
  PRIMARY KEY (`id_apartamento`),
  CONSTRAINT `nro_piso`
    FOREIGN KEY (`nro_piso`)
    REFERENCES `sia`.`piso` (`nro_piso`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE INDEX `nro_piso_idx` ON `sia`.`apartamento` (`nro_piso` ASC) VISIBLE;


-- -----------------------------------------------------
-- Table `sia`.`clase_residente`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sia`.`clase_residente` (
  `id_clase` INT NOT NULL,
  `descripcion` VARCHAR(60) NOT NULL,
  PRIMARY KEY (`id_clase`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `sia`.`residente`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sia`.`residente` (
  `ci` INT NOT NULL,
  `nombre` MEDIUMTEXT NOT NULL,
  `nacimiento` DATE NOT NULL,
  `telefono` INT(11) NOT NULL,
  `id_apartamento` INT NOT NULL,
  `clase` INT NOT NULL,
  PRIMARY KEY (`ci`),
  CONSTRAINT `id_apartamento`
    FOREIGN KEY (`id_apartamento`)
    REFERENCES `sia`.`apartamento` (`id_apartamento`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `clase`
    FOREIGN KEY (`clase`)
    REFERENCES `sia`.`clase_residente` (`id_clase`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE INDEX `id_apartamento_idx` ON `sia`.`residente` (`id_apartamento` ASC) VISIBLE;

CREATE INDEX `clase_idx` ON `sia`.`residente` (`clase` ASC) VISIBLE;


-- -----------------------------------------------------
-- Table `sia`.`tipos_ambiente`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sia`.`tipos_ambiente` (
  `id_tipo` INT NOT NULL AUTO_INCREMENT,
  `descripcion` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id_tipo`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `sia`.`ambiente`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sia`.`ambiente` (
  `id_ambiente` INT NOT NULL AUTO_INCREMENT,
  `tipo` INT NOT NULL,
  `apartamento` INT NOT NULL,
  PRIMARY KEY (`id_ambiente`),
  CONSTRAINT `tipo`
    FOREIGN KEY (`tipo`)
    REFERENCES `sia`.`tipos_ambiente` (`id_tipo`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `apartamento`
    FOREIGN KEY (`apartamento`)
    REFERENCES `sia`.`apartamento` (`id_apartamento`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE INDEX `tipo_idx` ON `sia`.`ambiente` (`tipo` ASC) VISIBLE;

CREATE INDEX `apartamento_idx` ON `sia`.`ambiente` (`apartamento` ASC) VISIBLE;


-- -----------------------------------------------------
-- Table `sia`.`servicio`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sia`.`servicio` (
  `cod_servicio` INT NOT NULL AUTO_INCREMENT,
  `descripcion` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`cod_servicio`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `sia`.`servicios_por_apartamento`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sia`.`servicios_por_apartamento` (
  `id` BIGINT(20) NOT NULL,
  `servicio_cod_servicio` INT NOT NULL,
  `id_apartamento` INT NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_servicio_has_apartamento_servicio1`
    FOREIGN KEY (`servicio_cod_servicio`)
    REFERENCES `sia`.`servicio` (`cod_servicio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_servicio_has_apartamento_apartamento1`
    FOREIGN KEY (`id_apartamento`)
    REFERENCES `sia`.`apartamento` (`id_apartamento`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE INDEX `fk_servicio_has_apartamento_apartamento1_idx` ON `sia`.`servicios_por_apartamento` (`id_apartamento` ASC) VISIBLE;

CREATE INDEX `fk_servicio_has_apartamento_servicio1_idx` ON `sia`.`servicios_por_apartamento` (`servicio_cod_servicio` ASC) VISIBLE;


-- -----------------------------------------------------
-- Table `sia`.`consumo`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sia`.`consumo` (
  `id` VARCHAR(45) NOT NULL,
  `fecha` DATE NOT NULL,
  `promedio` FLOAT NOT NULL,
  `servicios_por_departamento_id` BIGINT(20) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_consumo_servicio_has_apartamento1`
    FOREIGN KEY (`servicios_por_departamento_id`)
    REFERENCES `sia`.`servicios_por_apartamento` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `sia`.`sensor`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sia`.`sensor` (
  `id_sensor` INT NOT NULL AUTO_INCREMENT,
  `descripcion` VARCHAR(60) NOT NULL,
  PRIMARY KEY (`id_sensor`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `sia`.`uso_sensor`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sia`.`uso_sensor` (
  `ambiente` INT NOT NULL,
  `sensor` INT NOT NULL,
  CONSTRAINT `ambiente`
    FOREIGN KEY (`ambiente`)
    REFERENCES `sia`.`ambiente` (`id_ambiente`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `sensor`
    FOREIGN KEY (`sensor`)
    REFERENCES `sia`.`sensor` (`id_sensor`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE INDEX `ambiente_idx` ON `sia`.`uso_sensor` (`ambiente` ASC) VISIBLE;

CREATE INDEX `sensor_idx` ON `sia`.`uso_sensor` (`sensor` ASC) VISIBLE;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
