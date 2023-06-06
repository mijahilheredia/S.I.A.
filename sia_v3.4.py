#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import time
import pymysql
import speech_recognition as sr
import RPi.GPIO as GPIO
import pygame
from pygame.locals import *
import subprocess
import serial
import sensorTemp
import sensorHall
import tanque1
import tanque2
import consumoAgua
import botTelegram
import registrosSIA
import pdf
import ventana
import threading
import sys
from PyQt5 import QtWidgets, QtCore, QtGui

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setmode(GPIO.BCM)
GPIO.setup(24,GPIO.OUT)
GPIO.setup(23,GPIO.OUT)
GPIO.setup(27,GPIO.OUT)
GPIO.setup(22,GPIO.OUT)
GPIO.setup(20,GPIO.OUT)
GPIO.setup(21,GPIO.OUT)

#Aqui se establece la conexion con la base de datos
db = pymysql.connect(host="localhost",
                     user="root",
                     password="Zorro1530",
                     database="sia")
cursor = db.cursor()

class habitacion:
    """Contiene todas las funciones basicas de una habitacion general"""
    def __init__(self,id_hab):
        self.__id_hab=id_hab
        self.__luces_on=False
        self.t =  sensorTemp.sensorTemperatura()
        self.t.valDefine()
        self.__temperatura = int(self.t.devuelveTemperatura())
        #self.__puerta_open = sensorHall.magnetismo()
        self.__seguridad = False
        self.__ventilador_on = False
        self.__hora= datetime.datetime.now().strftime("%H"+":"+"%M"+":"+"%S")
        self.__hora_ctrl = int(datetime.datetime.now().strftime("%H"))
        self.__dic_h = {"00":"/home/pi/SIAauidos/ceroh.mp3","01":"/home/pi/SIAauidos/unah.mp3","02":"/home/pi/SIAauidos/dosh.mp3","03":"/home/pi/SIAauidos/tresh.mp3"
                        ,"04":"/home/pi/SIAauidos/cuatroh.mp3","05":"/home/pi/SIAauidos/cincoh.mp3","06":"/home/pi/SIAauidos/seish.mp3","07":"/home/pi/SIAauidos/sieteh.mp3"
                        ,"08":"/home/pi/SIAauidos/ochoh.mp3","09":"/home/pi/SIAauidos/nueveh.mp3","10":"/home/pi/SIAauidos/diezh.mp3","11":"/home/pi/SIAauidos/onceh.mp3"
                        ,"12":"/home/pi/SIAauidos/doceh.mp3","13":"/home/pi/SIAauidos/13h.mp3","14":"/home/pi/SIAauidos/14h.mp3","15":"/home/pi/SIAauidos/15h.mp3","16":"/home/pi/SIAauidos/16h.mp3"
                        ,"17":"/home/pi/SIAauidos/17h.mp3","18":"/home/pi/SIAauidos/18h.mp3","19":"/home/pi/SIAauidos/20h.mp3","20":"/home/pi/SIAauidos/20h.mp3","21":"/home/pi/SIAauidos/21h.mp3"
                        ,"22":"/home/pi/SIAauidos/22h.mp3","23":"/home/pi/SIAauidos/23h.mp3","24":"/home/pi/SIAauidos/24h.mp3","25":"/home/pi/SIAauidos/25h.mp3","26":"/home/pi/SIAauidos/26h.mp3"
                        ,"27":"/home/pi/SIAauidos/27h.mp3","28":"/home/pi/SIAauidos/28h.mp3","29":"/home/pi/SIAauidos/29h.mp3","30":"/home/pi/SIAauidos/30h.mp3"}

    def establecer_id(self,id_hab):
        self.__id_hab=id_hab
    def establecer_temperatura_estandar(self,temp):
        self.__temperatura=temp
    def establecer_estado_luces(self,luz):
        self.__luces_on = luz
    def obtener_id_hab(self):
        return self.__id_hab
    def obtener_estado_luces(self):
        return self.__luces_on
    def obtener_temperatura(self, dato):
        if dato == "temperatura":
            print("la temperatura ambiente es ",self.__temperatura," grados centigrados")
            registrosSIA.saveLog(self.__hora+":consulta temperatura, temp:"+str(self.__temperatura))
            if self.__temperatura < 30:
                pygame.mixer.music.load("/home/pi/SIAauidos/temp1.mp3")
                pygame.mixer.music.play(1)
                time.sleep(3)
                pygame.mixer.music.load(self.__dic_h[str(self.__temperatura)])
                pygame.mixer.music.play(1)
                time.sleep(1.5)
                pygame.mixer.music.load("/home/pi/SIAauidos/temp2.mp3")
                pygame.mixer.music.play(1)
        return self.__temperatura

    def obtener_estado_puerta(self):
        return sensorHall.magnetismo()
    
    def reporte_puerta(self):
        if self.__seguridad == True:
            if self.obtener_estado_puerta() == False:
                print("la puerta principal esta abierta")
                botTelegram.enviarMensajeTelegram("la puerta principal esta abierta")
                botTelegram.enviarMensajeTelegram("hora: "+self.__hora)
                botTelegram.enviarMensajeGrupal("hora: "+self.__hora+"\nla puerta principal esta abierta")
                registrosSIA.saveLog(self.__hora+" :Puerta principal abierta")
            
    def establecer_seguridad(self,dato):
        if dato == "activar seguridad" or dato == "activa la seguridad":
            self.__seguridad = True
            print("seguridad activada")
            registrosSIA.saveLog(self.__hora+":seguridad activada")
        elif dato == "Desactivar seguridad" or dato == "Desactiva la seguridad" or dato == "desactivar seguridad":
            self.__seguridad = False
            print("seguridad desactivada")
            registrosSIA.saveLog(self.__hora+"seguridad desactivada")
            
    
    def obtener_hora(self):
        return datetime.datetime.now().strftime("%H"+":"+"%M"+":"+"%S")

    def encendido_automatico(self):
        #Enciende de manera automatica la luz en una determinada hora
        if self.__hora_ctrl >= 18 or self.__hora_ctrl < 6:
            self.__luces_on = True
    
    def proceso_log_luz(self,dato):
        self.__resp = ""
        if dato == 22:
            self.__resp = "Dormitorio"
        elif dato == 23:
            self.__resp = "Baño"
        elif dato == 24:
            self.__resp = "Cocina"
        elif dato == 27:
            self.__resp = "Sala"
        return self.__resp

    def encendido_peticion(self,orden,dato):
        #Enciende la luz si es que se le ordena encenderlo
        self.__mensaje =""
        if orden == "off" and self.__luces_on == False:
            pygame.mixer.music.load("/home/pi/SIAauidos/luzReoff.mp3")
            pygame.mixer.music.play(1)
            self.__mensaje = "las luces ya estan apagadas"
            registrosSIA.saveLog(self.__hora+":"+self.proceso_log_luz(dato)+"-orden de apagado denegado")
        elif orden == "off" and self.__luces_on == True:
            self.establecer_estado_luces(False)
            pygame.mixer.music.load("/home/pi/SIAauidos/luzOff.mp3")
            pygame.mixer.music.play(1)
            GPIO.output(dato,GPIO.LOW)
            self.__mensaje = "luces apagadas"
            registrosSIA.saveLog(self.__hora+":"+self.proceso_log_luz(dato)+"-luces apagadas")
        elif orden == "on" and self.__luces_on == False:
            self.establecer_estado_luces(True)
            pygame.mixer.music.load("/home/pi/SIAauidos/luzOn.mp3")
            pygame.mixer.music.play(1)
            print(self.__luces_on)
            GPIO.output(dato,GPIO.HIGH)
            self.__mensaje = "luces encendidas"
            registrosSIA.saveLog(self.__hora+":"+self.proceso_log_luz(dato)+"-luces encendidas")
        elif orden == "on" and self.__luces_on == True:
            pygame.mixer.music.load("/home/pi/SIAauidos/luzReon.mp3")
            pygame.mixer.music.play(1)
            self.__mensaje = "las luces ya estan encendidas"
            registrosSIA.saveLog(self.__hora+":"+self.proceso_log_luz(dato)+"-orden de encendido denegado")
        print(self.__luces_on)
        return self.__mensaje

class dormitorio(habitacion):
    pass
    """la clase correspondiente a funciones especificas de un dormitorio"""
    def __init__(self,id_hab,nombres_hab):
        habitacion.__init__(self,id_hab)
        self.__nombres_hab = nombres_hab
        self.__horaAlarma = 0
        self.__minutoAlarma = 0
        self.__alarmaActiva = False
        self.__alarmaActivada = False
        self.__dic_hab = {"enciende la luz del dormitorio":"on","prende la luz del dormitorio":"on","luces dormitorio":"on"
                          ,"encender luz dormitorio":"on","apaga la luz del dormitorio":"off",
                          "apagar la luz del dormitorio":"off","fuera luces dormitorio":"off"}
        
        self.__dic_h = {"00":"/home/pi/SIAauidos/ceroh.mp3","01":"/home/pi/SIAauidos/unah.mp3","02":"/home/pi/SIAauidos/dosh.mp3","03":"/home/pi/SIAauidos/tresh.mp3"
                        ,"04":"/home/pi/SIAauidos/cuatroh.mp3","05":"/home/pi/SIAauidos/cincoh.mp3","06":"/home/pi/SIAauidos/seish.mp3","07":"/home/pi/SIAauidos/sieteh.mp3"
                        ,"08":"/home/pi/SIAauidos/ochoh.mp3","09":"/home/pi/SIAauidos/nueveh.mp3","10":"/home/pi/SIAauidos/diezh.mp3","11":"/home/pi/SIAauidos/onceh.mp3"
                        ,"12":"/home/pi/SIAauidos/doceh.mp3","13":"/home/pi/SIAauidos/13h.mp3","14":"/home/pi/SIAauidos/14h.mp3","15":"/home/pi/SIAauidos/15h.mp3","16":"/home/pi/SIAauidos/16h.mp3"
                        ,"17":"/home/pi/SIAauidos/17h.mp3","18":"/home/pi/SIAauidos/18h.mp3","19":"/home/pi/SIAauidos/20h.mp3","20":"/home/pi/SIAauidos/20h.mp3","21":"/home/pi/SIAauidos/21h.mp3"
                        ,"22":"/home/pi/SIAauidos/22h.mp3","23":"/home/pi/SIAauidos/23h.mp3","24":"/home/pi/SIAauidos/24h.mp3","25":"/home/pi/SIAauidos/25h.mp3","26":"/home/pi/SIAauidos/26h.mp3"
                        ,"27":"/home/pi/SIAauidos/27h.mp3","28":"/home/pi/SIAauidos/28h.mp3","29":"/home/pi/SIAauidos/29h.mp3","30":"/home/pi/SIAauidos/30h.mp3"}
        
    def establacer_habitante(self,nombres):
        self.__nombres_hab = nombres
    def obtener_nombres(self):
        return self.__nombres_hab
    
    def ejecutarOrden(self,orden):
        self.__respuesta = self.__dic_hab.get(orden,"nada en habitacion")
        print(self.encendido_peticion(self.__respuesta,22))
        print(self.obtener_estado_luces())

    def Alarma(self,mnsj):
        
        """Esta funcion define la hora de la alarma"""
        
        if(mnsj[0:17] == "Despiértame a las"):
            if(mnsj[20:21]==":"):
                self.__horaAlarma = int(mnsj[18:20])
                self.__minutoAlarma = int(mnsj[21:23])
            else:
                print(mnsj[18:19])
                self.__horaAlarma = int(mnsj[18:19])
                self.__minutoAlarma = int(mnsj[20:22])
            print("Alarma")
            print("hora: "+str(self.__horaAlarma))
            print("minuto: "+str(self.__minutoAlarma))
            registrosSIA.saveLog(self.obtener_hora()+":Alarma activada para las:"+str(self.__horaAlarma)+":"+str(self.__minutoAlarma))
            self.__alarmaActivada = True
            pygame.mixer.music.load("/home/pi/SIAauidos/activacionAlarm.mp3")
            pygame.mixer.music.play(1)
            time.sleep(2)
            self.__ha = None #variables auxiliares
            self.__ma = None
            if self.__minutoAlarma > 30:
                self.__ha = self.__horaAlarma+1
                self.__ma = 60-self.__minutoAlarma
                if self.__ha < 10:
                    pygame.mixer.music.load(self.__dic_h["0"+str(self.__ha)])
                    pygame.mixer.music.play(1)
                    time.sleep(1)
                else:
                    pygame.mixer.music.load(self.__dic_h[str(self.__ha)])
                    pygame.mixer.music.play(1)
                    time.sleep(1)
                pygame.mixer.music.load("/home/pi/SIAauidos/menosh.mp3")
                pygame.mixer.music.play(1)
                time.sleep(1)
            else:
                self.__ha = self.__horaAlarma
                self.__ma = self.__minutoAlarma
                if self.__ha < 10:
                    pygame.mixer.music.load(self.__dic_h["0"+str(self.__ha)])
                    pygame.mixer.music.play(1)
                    time.sleep(1)
                else:
                    pygame.mixer.music.load(self.__dic_h[str(self.__ha)])
                    pygame.mixer.music.play(1)
                    time.sleep(1)
                time.sleep(1)
                pygame.mixer.music.load("/home/pi/SIAauidos/horash.mp3")
                pygame.mixer.music.play(1)
            time.sleep(1)
            if self.__ma < 10:
                self.__ma = "0"+str(self.__ma)
            else:
                self.__ma = str(self.__ma)
            pygame.mixer.music.load(self.__dic_h[self.__ma])
            pygame.mixer.music.play(1)
            time.sleep(1)
            pygame.mixer.music.load("/home/pi/SIAauidos/minutosh.mp3")
            pygame.mixer.music.play(1)
        
    def verificacionAlarma(self):
        self.__h = int(datetime.datetime.now().strftime("%H")) and int(datetime.datetime.now().strftime("%H"))
        self.__m = int(datetime.datetime.now().strftime("%H")) and int(datetime.datetime.now().strftime("%M"))
        if self.__alarmaActivada == True:
            if self.__h == self.__horaAlarma:
                if self.__m == self.__minutoAlarma:
                    if self.__alarmaActiva == False:
                        self.__alarmaActiva = True
                        pygame.mixer.music.load("/home/pi/SIAauidos/despierta.mp3")
                        pygame.mixer.music.play(1)
                        time.sleep(5)
                        pygame.mixer.music.load("/home/pi/SIAmusic/musicaDespertar.mp3")
                        pygame.mixer.music.play(1)
                elif self.__m > self.__minutoAlarma:
                    self.__alarmaActiva = False
                    self.__alarmaActivada = False
                    self.__minutoAlarma = 0
                    self.__horaAlarma = 0 
            
        

class baño(habitacion):
    pass
    def __init__(self,id_ba):
        habitacion.__init__(self,id_ba)
        self.__ducha_on = False
        self.__dic_hab = {"enciende la luz del baño":"on","prende la luz del baño":"on","luces baño":"on"
                          ,"encender luz baño":"on","apaga la luz del baño":"off",
                          "apagar la luz del baño":"off","fuera luces baño":"off"}
        
        self.__dic_ducha = {"ducha":"on","enciende la ducha":"on","abre la ducha":"on"
                          ,"apaga la ducha":"off","cierra la ducha":"off"}

    def control_ducha(self,orden):
        self.__respuesta = self.__dic_ducha.get(orden,None)
        self.__mensaje =""
        if self.__respuesta == "off" and self.__ducha_on == False:
            pygame.mixer.music.load("/home/pi/SIAauidos/llaveReoff.mp3")
            pygame.mixer.music.play(1)
            self.__mensaje = "las ducha ya esta apagada"
            registrosSIA.saveLog(self.obtener_hora()+":ducha-orden de apagado denegado")
        elif self.__respuesta == "off" and self.__ducha_on == True:
            self.__ducha_on = False
            pygame.mixer.music.load("/home/pi/SIAauidos/llaveCerrar.mp3")
            pygame.mixer.music.play(1)
            GPIO.output(20,GPIO.LOW)
            self.__mensaje = "ducha apagada"
            registrosSIA.saveLog(self.obtener_hora()+":ducha apagada")
        elif self.__respuesta == "on" and self.__ducha_on == False:
            self.__ducha_on = True
            pygame.mixer.music.load("/home/pi/SIAauidos/llaveAgua.mp3")
            pygame.mixer.music.play(1)
            GPIO.output(20,GPIO.HIGH)
            self.__mensaje = "ducha encendida"
            registrosSIA.saveLog(self.obtener_hora()+":ducha encendida")
        elif self.__respuesta == "on" and self.__ducha_on == True:
            pygame.mixer.music.load("/home/pi/SIAauidos/llaveReon.mp3")
            pygame.mixer.music.play(1)
            self.__mensaje = "la ducha ya esta encendida"
            registrosSIA.saveLog(self.obtener_hora()+":ducha-orden de encendido denegado")
        print(self.__ducha_on)
        return self.__mensaje

    def ejecutarOrden(self,orden):
        self.__respuesta = self.__dic_hab.get(orden,None)
        print(self.encendido_peticion(self.__respuesta,23))
        print(self.obtener_estado_luces())
    
class cocina(habitacion):
    pass
    """Funciones basicas especificas de una cocina"""
    def __init__(self,id_co):
        habitacion.__init__(self,id_co)
        self.__valv_agua = False
        self.__detect_glp = False
        self.__detect_co = False
        self.__dic_hab = {"enciende la luz de la cocina":"on","prende la luz de la cocina":"on","luces cocina":"on"
                          ,"encender luz cocina":"on","apaga la luz de la cocina":"off",
                          "apagar la luz de la cocina":"off","fuera luces cocina":"off"}
        
        self.__dic_valv = {"abre la llave de la cocina":"on","enciende la llave de la cocina":"on","agua cocina":"on"
                          ,"apaga la llave de la cocina":"off",
                          "cierra la llave de la cocina":"off"}

    def verificacionFugaGLP(self, dato):
        if dato[0] == 'g':
            self.__pos = 3
            self.__d = 0
            if dato[self.__pos] == ':':
                self.__d = int(dato[self.__pos+1:-2])
            else:
                self.__pos = self.__pos+1
                if dato[self.__pos] == ':':
                    self.__d = int(dato[self.__pos+1:-2])
                
            print(self.__d)
            if self.__d > 150: #150
                self.__detect_glp = True
                registrosSIA.saveLog(self.obtener_hora()+":Deteccion de fuga de gas")
                botTelegram.enviarMensajeTelegram("Deteccion de fuga de gas")
                botTelegram.enviarMensajeTelegram("hora: "+self.obtener_hora())
                botTelegram.enviarMensajeGrupal("hora: "+self.obtener_hora()+"\nDeteccion de fuga de gas")
                pygame.mixer.music.load("/home/pi/SIAauidos/fugaGas.mp3")
                pygame.mixer.music.play(1)
                time.sleep(6)
                pygame.mixer.music.load("/home/pi/SIAauidos/ALARMA.mp3")
                pygame.mixer.music.play(1)
                time.sleep(1)
            elif self.__d < 150 and self.__detect_glp == True: #150
                self.__detect_glp = False
                registrosSIA.saveLog(self.obtener_hora()+":Ambiete estable, fuga de gas controlada")
                botTelegram.enviarMensajeTelegram("Ambiete estable, fuga de gas controlada")
                botTelegram.enviarMensajeTelegram("hora: "+self.obtener_hora())
                botTelegram.enviarMensajeGrupal("hora: "+self.obtener_hora()+"\nAmbiete estable, fuga de gas controlada")
                pygame.mixer.music.load("/home/pi/SIAauidos/estable.mp3")
                pygame.mixer.music.play(1)    

    def control_valv_agua(self,orden):
        self.__respuesta = self.__dic_valv.get(orden,None)
        self.__mensaje =""
        if self.__respuesta == "off" and self.__valv_agua == False:
            pygame.mixer.music.load("/home/pi/SIAauidos/llaveReoff.mp3")
            pygame.mixer.music.play(1)
            self.__mensaje = "las llave ya esta cerrada"
            registrosSIA.saveLog(self.obtener_hora()+":llave-orden de apagado denegado")
        elif self.__respuesta == "off" and self.__valv_agua == True:
            self.__valv_agua = False
            pygame.mixer.music.load("/home/pi/SIAauidos/llaveCerrar.mp3")
            pygame.mixer.music.play(1)
            GPIO.output(20,GPIO.LOW)
            self.__mensaje = "llave cerrada"
            registrosSIA.saveLog(self.obtener_hora()+":llave cerrada")
        elif self.__respuesta == "on" and self.__valv_agua == False:
            self.__valv_agua = True
            pygame.mixer.music.load("/home/pi/SIAauidos/llaveAgua.mp3")
            pygame.mixer.music.play(1)
            GPIO.output(20,GPIO.HIGH)
            self.__mensaje = "llave abierta"
            registrosSIA.saveLog(self.obtener_hora()+":llave abierta")
        elif self.__respuesta == "on" and self.__valv_agua == True:
            pygame.mixer.music.load("/home/pi/SIAauidos/llaveReon.mp3")
            pygame.mixer.music.play(1)
            self.__mensaje = "la llave ya esta abierta"
            registrosSIA.saveLog(self.obtener_hora()+":llave-orden de encendido denegado")
        print(self.__valv_agua)
        return self.__mensaje

    def ejecutarOrden(self,orden):
        self.__respuesta = self.__dic_hab.get(orden,"nada en cocina")
        print(self.encendido_peticion(self.__respuesta,27))
        print(self.obtener_estado_luces())

class sala(habitacion):
    pass
    """funciones basicas especificas que pueden haber en una sala"""
    def __init__(self,id_sala):
        habitacion.__init__(self,id_sala)
        self.__detect_co = False
        self.__dic_hab = {"enciende la luz de la sala":"on","prende la luz de la sala":"on","luces sala":"on"
                          ,"encender luz sala":"on","apaga la luz de la sala":"off",
                          "apagar la luz de la sala":"off","fuera luces sala":"off"}
        
        self.__dic_control = {"cambia de canal":"chUp","otro canal":"chUp","cambia de canal atras":"chD","baja canal":"chD",
                            "sube el volumen":"v+","aumenta el volumen":"v+","baja el volumen":"v-","disminuye el volumen":"v-"}

    def verificacionCO(self,dato):
        if dato[0] == 'c':
            self.__pos = 3
            self.__d = 0
            if dato[self.__pos] == ':':
                self.__d = int(dato[self.__pos+1:-2])
            else:
                self.__pos = self.__pos+1
                if dato[self.__pos] == ':':
                    self.__d = int(dato[self.__pos+1:-2])
                
            print(self.__d)
            if self.__d > 40: #50
                self.__detect_co = True
                registrosSIA.saveLog(self.obtener_hora()+":Deteccion de monoxido de carbono, posible incendio")
                botTelegram.enviarMensajeTelegram("Deteccion de monoxido de carbono, posible incendio")
                botTelegram.enviarMensajeTelegram("hora: "+self.obtener_hora())
                botTelegram.enviarMensajeGrupal("hora: "+self.obtener_hora()+"\nDeteccion de monoxido de carbono, posible incendio")
                pygame.mixer.music.load("/home/pi/SIAauidos/alarmaIncendio.mp3")
                pygame.mixer.music.play(1)
                time.sleep(6)
                pygame.mixer.music.load("/home/pi/SIAauidos/ALARMA.mp3")
                pygame.mixer.music.play(1)
                time.sleep(1)
            elif self.__d < 40 and self.__detect_co == True: #50
                self.__detect_co = False
                registrosSIA.saveLog(self.obtener_hora()+":ambiente estable, posible incendio controlado")
                botTelegram.enviarMensajeTelegram("Ambiete estable, posible incendio controlado")
                botTelegram.enviarMensajeTelegram("hora: "+self.obtener_hora())
                botTelegram.enviarMensajeGrupal("hora: "+self.obtener_hora()+"\nambiente estable, posible incendio controlado")
                pygame.mixer.music.load("/home/pi/SIAauidos/estable.mp3")
                pygame.mixer.music.play(1)
    
    def ejecutarOrden(self,orden):
        self.__respuesta = self.__dic_hab.get(orden,"nada en sala")
        print(self.encendido_peticion(self.__respuesta,24))
        print(self.obtener_estado_luces())
        
    def controlRemoto(self,orden):
        self.respuesta = self.__respuesta = self.__dic_control.get(orden,None)
        self.__control = False
        if self.respuesta == "chUp":
            subprocess.call("irsend SEND_ONCE SONY-TV KEY_CHANNELUP",shell=True)
            self.__control = True
        elif self.respuesta == "chD":
            subprocess.call("irsend SEND_ONCE SONY-TV KEY_CHANNELDOWN",shell=True)
            self.__control = True
        elif self.respuesta == "v+":
            subprocess.call("irsend SEND_ONCE SONY-TV KEY_VOLUMEUP",shell=True)
        elif self.respuesta == "v-":
            subprocess.call("irsend SEND_ONCE SONY-TV KEY_VOLUMEDOWN",shell=True)
            
        if self.__control == True:
            pygame.mixer.music.load("/home/pi/SIAauidos/cambioCanal.mp3")
            registrosSIA.saveLog(self.obtener_hora()+":tv-cambio de canal")
            pygame.mixer.music.play(1)

class musica():
    def __init__(self):
        self.__rock={"nirvana":"/home/pi/SIAmusic/nirvana.mp3","después de ti":"/home/pi/SIAmusic/Coda 3-Despues de ti.mp3","Hada y mago":"/home/pi/SIAmusic/rata blanca - la leyenda del hada y el mago.mp3",
                     "Mujer amante":"/home/pi/SIAmusic/Rata Blanca - Mujer Amante.mp3","religión":"/home/pi/SIAmusic/REM Losing My Religion.mp3"}
        self.__pop={"Zain":"/home/pi/SIAmusic/ZAYN-PILLOWTALK.mp3","Onion":"/home/pi/SIAmusic/on&on.mp3","body":"/home/pi/SIAmusic/Loud Luxury-Body.mp3",
                     "Jonas":"/home/pi/SIAmusic/fastCar.mp3","stay":"/home/pi/SIAmusic/Kygo-Stay.mp3"}
        self.__clasico={"Subidon":"/home/pi/SIAmusic/Fey-Subidon.mp3","Montaner":"/home/pi/SIAmusic/DEJAME LLORAR.mp3","eclipse":"/home/pi/SIAmusic/Eclipse Total Del Amor.mp3",
                       "Hijo de la luna":"/home/pi/SIAmusic/Mecano-Hijo de la luna.mp3","Sera":"/home/pi/SIAmusic/sera.mp3"}
        self.__reggaeton={"Adan y Eva":"/home/pi/SIAmusic/Adan y Eva.mp3","Adán y Eva":"/home/pi/SIAmusic/Adan y Eva.mp3","desconocidos":"/home/pi/SIAmusic/Desconocidos.mp3","otra vez":"/home/pi/SIAmusic/Otra Vez.mp3",
                          "por perro":"/home/pi/SIAmusic/POR PERRO.mp3","Sebastián":"/home/pi/SIAmusic/POR PERRO.mp3","Sebastian":"/home/pi/SIAmusic/POR PERRO.mp3",
                         "se preparó":"/home/pi/SIAmusic/Se Preparó.mp3"}
    def playMusica(self,text):
        print(text)
        self.__nombreCancion=""   #el metodo get nos permitira evitar una excepcion cuando no encuentre una clave
        if self.__rock.get(text,"nada")!="nada":
            self.__nombreCancion=self.__rock.get(text,"nada")
        elif self.__pop.get(text,"nada")!="nada":
            self.__nombreCancion=self.__pop.get(text,"nada")
        elif self.__clasico.get(text,"nada")!="nada":
            self.__nombreCancion=self.__clasico.get(text,"nada")
        elif self.__reggaeton.get(text,"nada")!="nada":
            self.__nombreCancion=self.__reggaeton.get(text,"nada")

        if self.__nombreCancion != "":
            registrosSIA.saveLog(":Reproduccion de cancion:"+self.__nombreCancion)
            pygame.mixer.music.load(self.__nombreCancion)
            pygame.mixer.music.play(1)
        
        

class residente:
    """En un apartamento viven familias o cualquier numero de personas
    esas personas tienen datos importantes para la gestion de una edificacion"""
    def __init__(self,nombre,ci,nacimiento,parent,celular):
        self.__nombre = nombre
        self.__ci = ci
        self.__nacimiento = nacimiento
        self.__parent = parent #es el parentezco que tienen con el propietario
        self.__cel = celular

    def establecer_cel(self,cel):
        self.__cel = cel
    def obtener_cel(self):
        return self.__cel

    def establecer_ci(self,ci):
        self.__ci = ci
    def obtener_ci(self):
        return self.__ci

    def establecer_nacimiento(self,nac):
        self.__nacimiento = nac
    def obtener_nacimiento(self):
        return self.__nacimiento

    def establecer_parent(self,p):
        self.__parent = p
    def obtener_parent(self):
        return self.__parent

    def establecer_nombre(self,n):
        self.__nombre = n
    def obtener_nombre(self):
        return self.__nombre

    def obtener_datos(self):
        print(self.__nombre,self.__ci,self.__nacimiento,self.__parent,self.__cel,sep = "\n")
        
    
class apartamento:
    """Aqui maneja menos funciones electronicas y mas funciones administrativas"""
    def __init__(self,nombre,ci,edad,hijos,nro_apa):
        #se define nombre del propietario(string),edad(int),carnet(int),hijos(True),
        #numero del apartamento(int)
        self.__nombre = nombre
        self.__ci = ci
        self.__edad = edad
        self.__hijos = hijos #Esta variable verifica si tiene hijos o no
        self.__nro_apa = nro_apa
        self.__nro_hab = 0
        self.__nro_resi = 0
        self.musica=musica()
        self.dor = []
        self.baño = []
        self.coc = []
        self.sala = []
        self.resi = []
        
    def print_datos(self):
        print(self.__nombre,self.__ci,self.__edad,self.__hijos,self.__nro_apa,self.__nro_hab,sep='\n')

    def establecer_nombre(self,nom):
        self.__nombre = nom
    def establecer_ci(self,ci):
        self.__ci=ci
    def establecer_edad(self,edad):
        self.__edad=edad
    def confirmar_hijos(self,conf):
        self.__hijos = conf
    def establecer__nro_apa(self,nro):
        self.__nro_apa = conf
        

    def obtener_nombre(self):
        return self.__nombre
    def obtener_ci(self):
        return self.__ci
    def obtener_edad(self):
        return self.__edad
    def obtener_hijos(self):
        return self.__hijos
    def obtener_nro_apa(self):
        return self.__nro_apa
    def obtener_nro_hab(self): #devuelve el numero de habitaciones
        return self.__nro_hab
    def obtener_nro_res(self): #devuelve el numero de residentes
        return self.__nro_resi
    
    def obtener_hora(self, orden):
        self.__hora= datetime.datetime.now().strftime("%H"+":"+"%M"+":"+"%S")
        self.__h = int(datetime.datetime.now().strftime("%H"))
        self.__min = int(datetime.datetime.now().strftime("%M"))
        self.__dic_hora = {"hora":self.__hora,"Dame la hora":self.__hora,"qué hora es":self.__hora,"qué hora tienes":self.__hora}
        self.__dic_h = {"00":"/home/pi/SIAauidos/ceroh.mp3","01":"/home/pi/SIAauidos/unah.mp3","02":"/home/pi/SIAauidos/dosh.mp3","03":"/home/pi/SIAauidos/tresh.mp3"
                        ,"04":"/home/pi/SIAauidos/cuatroh.mp3","05":"/home/pi/SIAauidos/cincoh.mp3","06":"/home/pi/SIAauidos/seish.mp3","07":"/home/pi/SIAauidos/sieteh.mp3"
                        ,"08":"/home/pi/SIAauidos/ochoh.mp3","09":"/home/pi/SIAauidos/nueveh.mp3","10":"/home/pi/SIAauidos/diezh.mp3","11":"/home/pi/SIAauidos/onceh.mp3"
                        ,"12":"/home/pi/SIAauidos/doceh.mp3","13":"/home/pi/SIAauidos/13h.mp3","14":"/home/pi/SIAauidos/14h.mp3","15":"/home/pi/SIAauidos/15h.mp3","16":"/home/pi/SIAauidos/16h.mp3"
                        ,"17":"/home/pi/SIAauidos/17h.mp3","18":"/home/pi/SIAauidos/18h.mp3","19":"/home/pi/SIAauidos/20h.mp3","20":"/home/pi/SIAauidos/20h.mp3","21":"/home/pi/SIAauidos/21h.mp3"
                        ,"22":"/home/pi/SIAauidos/22h.mp3","23":"/home/pi/SIAauidos/23h.mp3","24":"/home/pi/SIAauidos/24h.mp3","25":"/home/pi/SIAauidos/25h.mp3","26":"/home/pi/SIAauidos/26h.mp3"
                        ,"27":"/home/pi/SIAauidos/27h.mp3","28":"/home/pi/SIAauidos/28h.mp3","29":"/home/pi/SIAauidos/29h.mp3","30":"/home/pi/SIAauidos/30h.mp3"}
        if self.__dic_hora.get(orden,"nada")!="nada":
            print("Son las "+self.__dic_hora.get(orden,"nada"))
            registrosSIA.saveLog(self.baño[0].obtener_hora()+":consulta hora")
            pygame.mixer.music.load("/home/pi/SIAauidos/sonlash.mp3")
            pygame.mixer.music.play(1)  
            time.sleep(1)
            if self.__min > 30:
                print(str(self.__h+1))
                if self.__h+1 < 10:
                    pygame.mixer.music.load(self.__dic_h["0"+str(self.__h+1)])
                    pygame.mixer.music.play(1)
                    time.sleep(1)
                else:
                    pygame.mixer.music.load(self.__dic_h[str(self.__h+1)])
                    pygame.mixer.music.play(1)
                    time.sleep(1)
                pygame.mixer.music.load("/home/pi/SIAauidos/menosh.mp3")
                pygame.mixer.music.play(1)
                time.sleep(1)
                self.__min = 60 - self.__min
            else:
                pygame.mixer.music.load(self.__dic_h[datetime.datetime.now().strftime("%H")])
                pygame.mixer.music.play(1)
                time.sleep(1)
                pygame.mixer.music.load("/home/pi/SIAauidos/horash.mp3")
                pygame.mixer.music.play(1)
            time.sleep(1)
            if self.__min < 10:
                self.__min = "0"+str(self.__min)
            else:
                self.__min = str(self.__min)
            print(str(self.__min))
            pygame.mixer.music.load(self.__dic_h[self.__min])
            pygame.mixer.music.play(1)
            time.sleep(1)
            pygame.mixer.music.load("/home/pi/SIAauidos/minutosh.mp3")
            pygame.mixer.music.play(1)
            
#En esta funcion llenamos la relacion entre sensores y ambiente de la base de datos.
    def sensorxambiente(self):
        self.__tup1 = []
        self.__tup2 = []
        self.ps = 0
        cursor.execute("select * from ambiente")
        self.datos = cursor.fetchall()
        for data in self.datos:
            self.__tup1.append(data[0])
            self.__tup2.append(data[1])
        while (self.ps < len(self.__tup2)):
            self.__i =  str(self.__tup1[self.ps])
            if self.__tup2[self.ps] == 1:
                cursor.execute("insert into uso_sensor values("+self.__i+",2)")
                db.commit()
            elif self.__tup2[self.ps] == 2:
                cursor.execute("insert into uso_sensor values("+self.__i+",2)")
                db.commit()
                cursor.execute("insert into uso_sensor values("+self.__i+",3)")
                db.commit()
                cursor.execute("insert into uso_sensor values("+self.__i+",4)")
                db.commit()
                cursor.execute("insert into uso_sensor values("+self.__i+",8)")
                db.commit()
            elif self.__tup2[self.ps] == 3:
                cursor.execute("insert into uso_sensor values("+self.__i+",1)")
                db.commit()
                cursor.execute("insert into uso_sensor values("+self.__i+",2)")
                db.commit()
                cursor.execute("insert into uso_sensor values("+self.__i+",6)")
                db.commit()
            elif self.__tup2[self.ps] == 4:
                cursor.execute("insert into uso_sensor values("+self.__i+",5)")
                db.commit()
                cursor.execute("insert into uso_sensor values("+self.__i+",6)")
                db.commit()
                cursor.execute("insert into uso_sensor values("+self.__i+",7)")
                db.commit()
            self.ps=self.ps+1

#en estos metodo creamos la cantidad de dormitorios, baños, cocinas y sala que puede tener un apartamento
    
    def crear_dor(self,nro):
        self.copy = 0
        while self.copy < nro:
            self.dor.append(dormitorio(self.copy,""))
            cursor.execute("insert into ambiente(tipo,apartamento) values(1,"+str(self.__nro_apa)+")")
            db.commit()
            self.copy = self.copy+1
        self.__nro_hab = self.__nro_hab + nro
        
    def crear_baño(self,nro):
        self.copy = 0
        while self.copy < nro:
            self.baño.append(baño(self.copy))
            cursor.execute("insert into ambiente(tipo,apartamento) values(4,"+str(self.__nro_apa)+")")
            db.commit()
            self.copy = self.copy+1
        self.__nro_hab = self.__nro_hab+nro

    def crear_coc(self,nro):
        self.copy = 0
        while self.copy < nro:
            self.coc.append(cocina(self.copy))
            cursor.execute("insert into ambiente(tipo,apartamento) values(3,"+str(self.__nro_apa)+")")
            db.commit()
            self.copy = self.copy+1
        self.__nro_hab = self.__nro_hab+nro

    def crear_sala(self,nro):
        self.copy = 0
        while self.copy < nro:
            self.sala.append(sala(self.copy))
            cursor.execute("insert into ambiente(tipo,apartamento) values(2,"+str(self.__nro_apa)+")")
            db.commit()
            self.copy = self.copy+1
        self.__nro_hab = self.__nro_hab+nro

    def crear_resi(self,nro):
        self.copy = 0
        while self.copy < nro:
            self.resi.append(residente("",0,"","",0))
            self.copy = self.copy+1
        self.__nro_resi = nro
        
#este metodo genera un informe pdf de todos los residentes y lo envia a telegram
    def generarInforme(self,orden):
        self.__dic_inf = {"genera un informe de los residentes":"ok","genera un informe de los habitantes":"ok",
                          "manda un informe de los residentes":"ok","manda un informe de los habitantes":"ok","informe habitantes":"ok",
                          "informe residentes":"ok"}
        self.__respuesta = self.__dic_inf.get(orden,None)
        if self.__respuesta == "ok":
            pygame.mixer.music.load("/home/pi/SIAauidos/regResidentes.mp3")
            pygame.mixer.music.play(1)
            self.__doc = open("informeResidentes.txt",'w')
            self.__p = pdf.PDF()
            self.__doc.writelines("Lista de residentes")
            self.__cont = 0
            while self.__cont < self.__nro_resi:
                self.__doc.writelines("\n"+"Residente numero "+str(self.__cont+1))
                self.__doc.writelines("\n"+self.resi[self.__cont].obtener_nombre())
                self.__doc.writelines("\n"+str(self.resi[self.__cont].obtener_ci()))
                self.__doc.writelines("\n"+self.resi[self.__cont].obtener_nacimiento())
                self.__doc.writelines("\n"+self.resi[self.__cont].obtener_parent())
                self.__doc.writelines("\n"+str(self.resi[self.__cont].obtener_cel()))
                self.__doc.writelines("\n")
                self.__cont = self.__cont + 1
            self.__doc.close()
            self.__p.crearPDF("informeResidentes.txt","INFORME DE RESIDENTES")
            registrosSIA.saveLog(self.baño[0].obtener_hora()+":Solicitud de informe de residentes")
            botTelegram.enviarDocumento("Envio de registro de habitantes",'siaRegistro.pdf')
            
    def obtenerAyuda(self,orden):
        self.__res = self.baño[0].obtener_hora()+":Alguien pide auxilio de manera urgente en la casa, puede estar en problemas"
        self.__dic_help = {"estoy herido":self.__res,"auxilio":self.__res,
                          "pide ayuda":self.__res}
        if orden in self.__dic_help:
            pygame.mixer.music.load("/home/pi/SIAauidos/auxilio.mp3")
            pygame.mixer.music.play(1)
            botTelegram.enviarMensajeGrupal(self.__dic_help[orden])
            
#los siguientes metodos son para añadir o quitar un elemento desde un dormitorio hasta

    def añadir_dor(self,nro):
        self.dor.append(dormitorio(self.copy,""))

    def añadir_baño(self,nro):
        self.baño.append(baño(0))

    def añadir_coc(self,nro):
        self.coc.append(cocina(0))

    def añadir_sala(self,nro):
        self.sala.append(dormitorio(0))

class piso:
    """el piso administrara la cantidad de habitaciones que existe y el control de algunas valvulas"""
    def __init__(self):
        self.__nro_piso=0
        self.__termico = True
        self.__valvula_agua = True
        self.__estadoTanque = None
        self.__valvula_gas = True
        self.__vol_tanque = 3.458 #litros
        self.__nro_apa = 0
        self.apar = []

    def establecer_nro_piso(self,nro):
        self.__nro_piso=nro
        
    def control_termico(self,orden):
        self.__termico = orden
    def obtener_estado_termico(self):
        return self.__termico

    def control_valv_agua(self,orden):
        self.__valvula_agua = orden
    def obtener_estado_valv_agua(self):
        return self.__valvula_agua
    
    def control_valv_gas(self,orden):
        self.__valvula_gas = orden
    def obtener_estado_valv_gas(self):
        return self.__valvula_gas

    def crear_apartamentos(self,nro):
        self.copy = 0
        self.base_nro = self.__nro_piso*10;
        while self.copy < nro:
            self.apar.append(apartamento("",0,0,False,self.base_nro+self.copy+1))
            self.__id=self.base_nro+self.copy+1
            cursor.execute("insert into apartamento(id_apartamento,nro_piso) values("+str(self.__id)+","+str(self.__nro_piso)+")")
            db.commit()
            self.__id2 = (self.__id*10)+1
            cursor.execute("insert into servicios_por_apartamento values("+str(self.__id2)+",1,"+str(self.__id)+")")
            db.commit()
            cursor.execute("insert into servicios_por_apartamento values("+str(self.__id2+1)+",2,"+str(self.__id)+")")
            db.commit()
            cursor.execute("insert into servicios_por_apartamento values("+str(self.__id2+2)+",4,"+str(self.__id)+")")
            db.commit()
            self.copy = self.copy+1
        self.__nro_apa = nro
        
    def reporte_tanque(self):
        if(tanque1.estado()==True and tanque2.estado()==False):
            print("el tanque esta vacio")
            registrosSIA.saveLog(self.apar[0].baño[0].obtener_hora()+":tanque vacio")
            self.__estadoTanque = False
            pygame.mixer.music.load("/home/pi/SIAauidos/llenarTanque.mp3")
            pygame.mixer.music.play(1)
            self.llenarTanque(True)
            GPIO.output(21,GPIO.HIGH)
        elif(tanque1.estado()==False and tanque2.estado()==True):
            if self.__estadoTanque == False:
                self.__estadoTanque = True
                print("el tanque esta lleno")
                registrosSIA.saveLog(self.apar[0].baño[0].obtener_hora()+":tanque lleno")
                self.llenarTanque(False)
                pygame.mixer.music.load("/home/pi/SIAauidos/tanqueLleno.mp3")
                pygame.mixer.music.play(1)
                GPIO.output(21,GPIO.LOW)
        
    def llenarTanque(self, dato):
        if dato==True:
            print("llenando tanque")
            registrosSIA.saveLog(self.apar[0].baño[0].obtener_hora()+":llenando tanque")
        elif dato == False:
            print("parando llenado")
            self.fechaActual = datetime.datetime.today().strftime('%Y-%m-%d')
            cursor.execute("insert into consumo values('SA-"+str(datetime.datetime.today())+"','"+self.fechaActual+"',"+str(self.__vol_tanque)+",112)")
            db.commit()
            registrosSIA.saveLog(self.apar[0].baño[0].obtener_hora()+":tanque lleno")
            
    def reporteConsumos(self,orden):
        self.__dic_cons = {"genera un informe del consumo de agua":"ok","genera un informe del agua":"ok","informe agua":"ok",
                          "manda un informe del agua":"ok","manda un informe del servicio de agua":"ok","informe de consumo de agua":"ok",
                          "informe del consumo de servicio de agua":"ok"}
        self.__respuesta = self.__dic_cons.get(orden,None)
        if self.__respuesta == "ok":
            pygame.mixer.music.load("/home/pi/SIAauidos/regConAgua.mp3")
            pygame.mixer.music.play(1)
            self.__tup1 = []
            self.__tup2 = []
            self.ps = 0
            cursor.execute("select * from consumo")
            self.datos = cursor.fetchall()
            for data in self.datos:
                self.__tup1.append(data[1])
                self.__tup2.append(data[2])
            self.__mes = str(self.__tup1[0])[0:7]
            self.__comp = str(self.__tup1[0])[8:10]
            self.__total = 0
            while (self.ps < len(self.__tup1)):
                self.__aux = str(self.__tup1[self.ps])[8:10]
                if  self.__aux == self.__comp:
                    self.__total = self.__total + float(self.__tup2[self.ps])
                else:
                    consumoAgua.addConsDia(int(self.__comp),self.__total)
                    self.__comp = str(self.__tup1[self.ps])
                    self.__total = 0
                self.ps = self.ps+1
            consumoAgua.addConsDia(int(self.__comp),self.__total)
            consumoAgua.addConsDia(int(self.__comp)+1,0)
            consumoAgua.crearPDF(self.__mes)
            registrosSIA.saveLog(self.apar[0].baño[0].obtener_hora()+":Solicitud de informe de consumo de agua")
            botTelegram.enviarDocumento("Envio de informe de consumo",'consumoAgua'+self.__mes+'.pdf')
            botTelegram.enviarDocGrupal("Envio de informe de consumo",'consumoAgua'+self.__mes+'.pdf')
        


#Aqui es donde comienza la mas importante de las clases, la matriz de todo, S.I.A. que significa sistema de inteligencia artificial, no solo es un asistente virtual
#Si no que tambien es capaz de realizar tareas de domotica e inmotica,
        
class sia:
    """Aqui se debe controlar todo el sistema"""
    def __init__(self):
        self.__nombre = "Alejandra"
        self.__nom_prop = ""
        self.__nom_edif = ""
        self.__pasword = ""
        self.__direccion = ""
        self.__configurado = False
        self.__com_serial = serial.Serial('/dev/ttyUSB0',baudrate=9600,bytesize=8,parity='N',stopbits=1)
        self.piso = []
        self.__msnWindow = "" #aqui se guarda el mensaje para la interfaz grafica
        pygame.init()
        
    def reconocer(self):
        self.__mens=""
        self.__r = sr.Recognizer()
        with sr.Microphone() as source:
                print("te escucho")
                try:
                    self.__audio = self.__r.listen(source,2) #te escuchara por durante 2 segundos
                except sr.WaitTimeoutError as e:
                    self.__mens = "tiempo"
                    
        if self.__mens != "tiempo": #existe una excepcion si es que se quitara este if, porfavor no quitar
            try:
                self.__mens = self.__r.recognize_google(self.__audio, language = "es-ES")
                
            except sr.UnknownValueError:
                self.mens = "lo siento no pude entenderte"
                    
        return self.__mens

#Sia tiene un nombre por defecto, su nombre es Alejandra, como en cualquier conversacion, primero debes mencionar el nombre de la
#persona o en este caso del agente,esto para evitar mencionar alguna palabra clave durante una conversacion con otras personas y
#SIA ejecute alguna funcion
    
    def escuharMiNombre(self):
        if self.__configurado == True: #esta variable se mantiene en true cuando esta configurado
            while True:
                self.__escuchado = self.reconocer()
                if self.__escuchado == self.__nombre:
                    print(self.__escuchado)
                    pygame.mixer.music.load("/home/pi/SIAauidos/resp1.wav")
                    pygame.mixer.music.play(1)
                    self.escucharOrden()
                else:
                    print(self.lectura())
                    self.piso[0].apar[0].dor[0].verificacionAlarma()
                    self.piso[0].apar[0].coc[0].verificacionFugaGLP(self.lectura()[0])
                    self.piso[0].apar[0].sala[0].verificacionCO(self.lectura()[1])
                    self.piso[0].apar[0].sala[0].reporte_puerta()
                    self.piso[0].reporte_tanque()

        else:
            self.configuracion_inicial()

    def escucharOrden(self):
        while True:
            self.__escuchado = self.reconocer()
            print(self.__escuchado)
            self.piso[0].apar[0].musica.playMusica(self.__escuchado)
            self.piso[0].apar[0].dor[0].ejecutarOrden(self.__escuchado)
            self.piso[0].apar[0].baño[0].ejecutarOrden(self.__escuchado)
            self.piso[0].apar[0].coc[0].ejecutarOrden(self.__escuchado)
            self.piso[0].apar[0].sala[0].ejecutarOrden(self.__escuchado)
            self.piso[0].apar[0].baño[0].control_ducha(self.__escuchado)
            self.piso[0].apar[0].coc[0].control_valv_agua(self.__escuchado)
            self.piso[0].apar[0].sala[0].establecer_seguridad(self.__escuchado)
            self.piso[0].apar[0].sala[0].controlRemoto(self.__escuchado)
            self.piso[0].apar[0].obtener_hora(self.__escuchado)
            self.piso[0].apar[0].generarInforme(self.__escuchado)
            self.piso[0].apar[0].obtenerAyuda(self.__escuchado)
            self.piso[0].apar[0].dor[0].Alarma(self.__escuchado)
            self.piso[0].apar[0].dor[0].obtener_temperatura(self.__escuchado)
            self.piso[0].reporteConsumos(self.__escuchado)
            self.generarInformeRegistros(self.__escuchado)
            #print(self.piso[0].apar[0].dor[0].obtener_estado_luces())
            self.escuharMiNombre()
        
    def lectura(self):
        self.__respuestaS1 = self.__com_serial.readline().decode()
        time.sleep(0.2)
        self.__respuestaS2 = self.__com_serial.readline().decode()
        self.__com_serial.flushInput()
        return (self.__respuestaS1,self.__respuestaS2)

    def crear_pisos(self,nro):
        self.copy = 0
        self.desc = ''
        if nro <= 1:
            self.desc = 'planta baja'
        else:
            self.desc = 'piso '+str(nro) 
        while self.copy < nro:
            self.piso.append(piso())
            self.piso[self.copy].establecer_nro_piso(self.copy+1)
            self.copy = self.copy+1
            cursor.execute("insert into piso(decripcion) values('"+self.desc+f"')")
            db.commit()
        self.__nro_piso = nro

    def configuracion_inicial(self):
        pygame.mixer.music.load("/home/pi/SIAauidos/mensaje1.wav")
        pygame.mixer.music.play(1)
        print("","","¡¡¡BIENVENIDO A LA CONFIGURACION MANUAL ORIENTADA!!!",
              "El sistema se ha iniciado por primera vez asi que comenzaremos ingresando el nombre del propietario",
              "y su respectiva contraseña","","Ingrese el nombre completo del propietario",sep='\n')
        self.__dato = input()
        self.establecer_propietario(self.__dato)
        
        self.__nro_try = 3
        self.__copy = ""
        while self.__dato != self.__copy:
            if self.__nro_try < 0:
                pygame.mixer.music.load("/home/pi/SIAauidos/mensAdv3.wav")
                pygame.mixer.music.play(1)
                print("numero de intentos superados","estableciendo contraseña por defecto","contraseña: 1234",sep='\n')
                self.__dato = "1234"
                break
            pygame.mixer.music.load("/home/pi/SIAauidos/msj2.wav")
            pygame.mixer.music.play(1)
            print("Ingrese una nueva contraseña")
            self.__dato = input()
            self.__copy = self.__dato
            pygame.mixer.music.load("/home/pi/SIAauidos/msj3.wav")
            pygame.mixer.music.play(1)
            print("Repita la contraseña")
            self.__dato = input()
            self.__nro_try = self.__nro_try - 1
            
        self.__establecer_contraseña(self.__dato)
        pygame.mixer.music.load("/home/pi/SIAauidos/msj4.wav")
        pygame.mixer.music.play(1)
        print("Ingrese el tipo de edificacion","1:Domicilio particular","   Edificacion pequeña donde habita una sola familia",
              "2:Otros","   Edificacion construida para albergar varias familias, como ser residencial,condominio,edificio,etc",sep='\n')
        self.__dato = input()
        while True:
            if self.__dato == "1":
                break
            elif self.__dato == "2":
                break
            else:
                pygame.mixer.music.load("/home/pi/SIAauidos/msjAdv4.wav")
                pygame.mixer.music.play(1)
                print("por favor ingrese un numero de las opciones mostradas")
                self.__dato = input()
                
        if self.__dato == "1":
            self.__configuracion_casa()
        elif self.__dato == "2":
            self.__configuracion_edificio()

        pygame.mixer.music.load("/home/pi/SIAauidos/msjpres.wav")
        pygame.mixer.music.play(1)
        print(" "," ","Se ha finalizado la configuracion",
              "Hola mi nombre es Alejandra y soy tu asistente virtual, di mi nombre si es que necesitas algo",sep='\n')
        self.__configurado = True
        self.escuharMiNombre()
        
        
    def establecer_nom_edif(self,nom):
        #metodo que define el nombre de la edificacion
        self.__nom_edif = nom

    def establecer_propietario(self,prop):
        self.__nom_prop = prop

    def __establecer_contraseña(self,contra):
        self.__pasword = contra

    def establecer_direccion(self,direc):
        self.__direccion = direc

#define la configuracion  inicial de la casa
    def __configuracion_casa(self):
        self.crear_pisos(1)
        self.piso[0].crear_apartamentos(1)
        self.piso[0].apar[0].establecer_nombre(self.__nom_prop)
        pygame.mixer.music.load("/home/pi/SIAauidos/msj5_1.wav")
        pygame.mixer.music.play(1)
        print(" ","Configuracion de domicilio particular iniciada",
              "sr: "+self.__nom_prop+" ingrese su carnet de identidad",sep='\n')
        self.__dato = int(input())
        cursor.execute("insert into residente(ci,nombre,id_apartamento,clase) values("+str(self.__dato)+",'"+self.__nom_prop+"',11,1)")
        db.commit()
        self.piso[0].apar[0].establecer_ci(self.__dato)
        pygame.mixer.music.load("/home/pi/SIAauidos/msj5_2.wav")
        pygame.mixer.music.play(1)
        print("por favor indique la cantidad de habitantes que viven dentro de esta casa incluyendose a usted")
        self.__dato = int(input())
        self.piso[0].apar[0].crear_resi(self.__dato)
        pygame.mixer.music.load("/home/pi/SIAauidos/msj5_3.wav")
        pygame.mixer.music.play(1)
        print("Acabemos añadiendo algunos datos personales","Ingrese su fecha de nacimiento (Formato aaaa-mm-dd)",sep='\n')
        self.__fn = input()
        cursor.execute("update residente set nacimiento = '"+self.__fn+"' where ci="+str(self.piso[0].apar[0].obtener_ci()))
        db.commit()
        pygame.mixer.music.load("/home/pi/SIAauidos/msj5_4.wav")
        pygame.mixer.music.play(1)
        print("Ingrse su numero de celular")
        self.__cel = int(input())
        cursor.execute("update residente set telefono = "+str(self.__cel)+" where ci="+str(self.piso[0].apar[0].obtener_ci()))
        db.commit()
        cursor.execute("update apartamento set propietario = '"+self.__nom_prop+"' where id_apartamento=11")
        db.commit()
        self.piso[0].apar[0].resi[0] = residente(self.__nom_prop,self.piso[0].apar[0].obtener_ci(),self.__fn,"Propietario",self.__cel)
        print("Estos son sus datos personales")        
        self.piso[0].apar[0].resi[0].obtener_datos()
        pygame.mixer.music.load("/home/pi/SIAauidos/msj5_6.wav")
        pygame.mixer.music.play(1)
        print("¿Desea registrar al resto de los habitantes?","   1:si","   2:no",sep='\n')
        self.__dato = input()
        if self.__dato == "1":
            self.__nro = self.piso[0].apar[0].obtener_nro_res()
            self.__cont = 1
            while self.__cont < self.__nro:
                pygame.mixer.music.load("/home/pi/SIAauidos/msj5_7.wav")
                pygame.mixer.music.play(1)
                print(" ","registrando al siguiente habitante",sep='\n')
                print("Ingrese un nombre")
                self.__n = input()
                pygame.mixer.music.load("/home/pi/SIAauidos/msj5_8.wav")
                pygame.mixer.music.play(1)
                print("Ingrese el carnet de identidad correspondiente al nombre")
                self.__ci = int(input())
                pygame.mixer.music.load("/home/pi/SIAauidos/msj5_9.wav")
                pygame.mixer.music.play(1)
                print("Ingrese la fecha de nacimiento (Formato aaaa-mm-dd)")
                self.__fn = input()
                pygame.mixer.music.load("/home/pi/SIAauidos/msj5_10.wav")
                pygame.mixer.music.play(1)
                print("Ingrese el parentezco con el propietario")
                self.__p = input()
                self.__clase_p = 0
                if(self.__p=="esposo" or self.__p=="esposa"):
                    self.__clase_p = 2
                elif(self.__p=="madre" or self.__p=="mama"):
                    self.__clase_p = 3
                elif(self.__p=="padre" or self.__p=="papa"):
                    self.__clase_p = 4
                elif(self.__p=="hermano" or self.__p=="hermana"):
                    self.__clase_p = 5
                elif(self.__p=="primo" or self.__p=="prima"):
                    self.__clase_p = 6
                elif(self.__p=="tio" or self.__p=="tia"):
                    self.__clase_p = 7
                elif(self.__p=="suegro" or self.__p=="suegra"):
                    self.__clase_p = 8
                elif(self.__p=="pareja"):
                    self.__clase_p = 9
                elif(self.__p=="inquilino"):
                    self.__clase_p = 10
                else:
                    self.__clase_p = 11
                pygame.mixer.music.load("/home/pi/SIAauidos/msj5_11.wav")
                pygame.mixer.music.play(1)
                print("Ingrese un numero de celular relacionado a esta persona")
                self.__cel = int(input())
                self.piso[0].apar[0].resi[self.__cont] = residente(self.__n,self.__ci,self.__fn,self.__p,self.__cel)
                cursor.execute("insert into residente values("+str(self.__ci)+",'"+self.__n+"','"+self.__fn+"',"+str(self.__cel)+",11,"+str(self.__clase_p)+")")
                db.commit()
                pygame.mixer.music.load("/home/pi/SIAauidos/msj5_12.wav")
                pygame.mixer.music.play(1)
                print(" ","Estos son los datos registrados"," ",sep='\n')
                self.piso[0].apar[0].resi[self.__cont].obtener_datos()
                self.__cont = self.__cont + 1
                
        pygame.mixer.music.load("/home/pi/SIAauidos/msj7.wav")
        pygame.mixer.music.play(1)
        print("¡¡¡MUY BIEN!!!, ahora seguiremos con la configuracion de la infraestructura",
              "Ingrese la cantidad de DORMITORIOS que tiene su casa",sep='\n')
        self.__dato = int(input())
        self.piso[0].apar[0].crear_dor(self.__dato)
        pygame.mixer.music.load("/home/pi/SIAauidos/msj8.wav")
        pygame.mixer.music.play(1)
        print("Ingrese la cantidad de BAÑOS que hay en la casa")
        self.__dato = int(input())
        self.piso[0].apar[0].crear_baño(self.__dato)
        pygame.mixer.music.load("/home/pi/SIAauidos/msj9.wav")
        pygame.mixer.music.play(1)
        print("Ingrese la cantidad de COCINAS que hay en la casa")
        self.__dato = int(input())
        self.piso[0].apar[0].crear_coc(self.__dato)
        pygame.mixer.music.load("/home/pi/SIAauidos/msj10.wav")
        pygame.mixer.music.play(1)
        print("Ingrese la cantidad de SALAS que hay en la casa")
        self.__dato = int(input())
        self.piso[0].apar[0].crear_sala(self.__dato)
        self.piso[0].apar[0].sensorxambiente()
             

    def __configuracion_edificio(self):
        print("Se comenzara definiendo la cantidad de pisos que existe en este edificio",
              "indique la cantidad de pisos que existe en el edificio",sep='\n')
        self.__p = int(input())
        self.crear_pisos(self.__p)
        print("Indique la cantidad de apartamentos que tiene cada piso")
        self.__contador = 0
        while self.__p > self.__contador:
            print("indique la cantidad de apartamentos que existe en el piso: ",self.__contador+1)
            self.__a = int(input())
            self.piso[self.__contador].crear_apartamentos(self.__a)
            self.__contador = self.__contador+1
        print("Ha terminado la configuracion inicial del edificio",
              " si desea personalizar cada apartamento en particular o registrar a habitantes en algun apartamento",
              "solamente pronuncie la palabra: CONFIGURACION y se le mostrara una serie de opciones")
    
    def generarInformeRegistros(self,orden):
        self.__dic_inf = {"genera un informe de activades":"ok","genera un informe general":"ok",
                          "manda un informe de actividades":"ok","manda un informe general":"ok","informe general":"ok",
                          "registro de actividades":"ok","informe de actividades":"ok"}
        self.__respuesta = self.__dic_inf.get(orden,None)
        if self.__respuesta == "ok":
            pygame.mixer.music.load("/home/pi/SIAauidos/regGeneral.mp3")
            pygame.mixer.music.play(1)
            registrosSIA.saveLog(self.piso[0].apar[0].baño[0].obtener_hora()+":Solicitud de informe de actividades general")
            self.__fecha = datetime.datetime.now().strftime("%d-%m-%y")
            self.__nombre ="sia"+self.__fecha+".log"
            self.__p = pdf.PDF()
            self.__p.crearPDF(self.__nombre,"INFORME DE REGISTRO DE ACTIVIDADES")
            botTelegram.enviarDocumento("Envio de registro de actividades",'siaRegistro.pdf')
            
    def setMensaje(self,dato):
        self.__msnWindow = dato
        
    def getMensaje(self):
        return self.__msnWindow
    
s = sia()
s.escuharMiNombre()

