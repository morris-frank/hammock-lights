#!/bin/python

#For the moving average
from collections import deque
#For measurements from the sensors
import time
#For the SDFT
import numpy as np
#For concurrent call to the sensors
from threading import Thread
#The pigpio library
import pigpio
#For cls
import os

#Number of elements in the moving average
MASIZE = 30

#Number of elements in the sliding distinct fourier transformation
DFTSIZE = 2**8

#Distance between to point in the SDFT in ms
GRIDDIST = 30

#Time between triggers in ms
TRIGTIME = 200

#The raspberry to use
pi = pigpio.pi()

#The latest measurements, has to be global
latest = dict()

#------------------------------------------------------------------------------

clear = lambda: os.system('cls')

def LinearInterpolation(leftTime, rightTime, leftMeasure, rightMeasure):
    slope = (rightMeasure - leftMeasure) / (rightTime - leftTime)
    return GRIDDIST * slope + leftMeasure


class DistSensor:
    """class DistSensor is for a HC-SR04 Sensor"""
    def __init__(self, name, echo, trigger):
        self.name = name
        self.echo = echo
        pi.set_mode(echo, pigpio.INPUT)
        self.trigger = trigger
        pi.set_mode(trigger, pigpio.OUTPUT)

    def measure(self):
        pi.write(self.trigger, 1)
        tim.sleep(0.00001)
        pi.write(self.trigger, 0)

        start = time.time()
        end = time.time()

        while pi.read(self.echo) == 0:
            start = time.time()

        while pi.read(self.echo) == 1:
            end = time.time()

        timeDelta = end - start
        dist = (timeDelta * 34300) / 2

        #The estimated time point of the measurement
        measureTime = (start + end) / 2

        latest[self.name]= (int(measureTime), dist)
        return latest[self.name]


class MovingAverage(deque):
    """MovingAverage is self explanatory"""
    def __init__(self, *args):
        deque.__init__(self, [], MASIZE)
        self.average = 0.0

    def append(self, pnt):
        n = len(self)
        if n == MASIZE:
            self.average -= deque.popleft(self) / MASIZE
            self.average += float(pnt) / MASIZE
        else:
            self.average *= float(n) / (n + 1)
            self.average += float(pnt) / (n + 1)
        deque.append(self, append)


class SensorVector:
    def __init__(self):
        self.sensorList = dict()
        self.movingAverages = dict()

    def append(self, name, sensor):
        self.sensorList[name] = sensor
        self.movingAverages[name] = MovingAverage()
        latest[name] = (0.0, 0.0)

    def measure(self):
        overallMeasure = 0.0
        overallTime = 0
        usedSensors = 0
        threads = [Thread(target=self.sensorList[name].measure(), args=())
                        for name in self.sensorList]
        _ = [t.start() for t in threads]
        _ = [t.join() for t in threads]
        for sensor in self.sensorList:
            self.movingAverages[sensor].append(latest[sensor][1])
            if latest[sensor][1] != 0:
                overallMeasure += latest[sensor][1] - self.movingAverages[sensor].average
                overallTime += latest[sensor][0]
                usedSensors += 1
        return (overallTime/usedSensors, overallMeasure/usedSensors)


class SDFT:
    def __init__(self, interpolFunc):
        self.newestMeasureTime = time.time()
        self.newestMeasure = 0
        self.oldestMeasure = 0
        self.interpolFunc = interpolFunc
        self.freqs = np.zeros(DFTSIZE + 1)
        self.measures = np.zeros(DFTSIZE)
        self.coeffs = np.zeros(DFTSIZE, dtype=np.complex)
        self.index = 0
        initCoeffs()

    def initCoeffs(self):
        for i in range(DFTSIZE):
            a = -2.0 * np.pi * i / float(DFTSIZE)
            self.coeffs[i] = complex(np.cos(a), np.sin(a))

    def append(self, measure):
        interMeasure = self.interpolFunc(self.newestMeasureTime, measure[0],
                                                       self.newestMeasure, measure[1])
        self.measures[self.index + 1]  = self.newestMeasure = measure[1]
        self.newestMeasureTime = measure[0]
        delta = complex(self.newestMeasure - self.measures[self.index])
        ci = 0
        for i in range(DFTSIZE):
            freqs[i] += delta * self.coeffs[ci]
            ci += self.index
            if ci >= DFTSIZE:
                ci -= DFTSIZE
        self.index += 1
        if self.index == DFTSIZE:
            self.index = 0


class Hammock:
    def __init__(self, sensors):
        self.sdft = SDFT(LinearInterpolation)
        self.sensors = sensors

    def start(self):
        while True:
            self.iter()
            time.sleep(TRIGTIME)

    def iter(self):
        self.sdft.append(self.sensors.measure())
        clear()
        print(self.sdft.freqs)


def __main__():
    sensors = SensorVector()
    sensors.append('BACK', DistSensor('BACK', 24, 18))
    sensors.append('FRONT', DistSensor(,'FRONT', 16, 26))
    hammock = Hammock(sensors)




