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
MASIZE = 300

#Number of elements in the sliding distinct fourier transformation
DFTSIZE = 2**8

#Distance between to point in the SDFT in ms
GRIDDIST = 30

#Time between triggers in ms
TRIGTIME = 100

#The raspberry to use
pi = pigpio.pi()

#The latest measurements, has to be global
latest = dict()

#------------------------------------------------------------------------------

clear = lambda: os.system('clear')

def LinearInterpolation(leftTime, rightTime, leftMeasure, rightMeasure):
    if rightTime > leftTime:
        slope = (rightMeasure - leftMeasure) / (rightTime - leftTime)
        return GRIDDIST * slope + leftMeasure
    else:
        print "iterError"
        return rightMeasure


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
        time.sleep(0.00001)
        pi.write(self.trigger, 0)

        start = time.time()
        end = time.time()

        hi = 0
        while pi.read(self.echo) == 0 and hi < 20:
            start = time.time()
            hi += 1

        if hi >= 20:
            latest[self.name] = (int(0), 0)
            return False

        while pi.read(self.echo) == 1:
            end = time.time()

        timeDelta = end - start
        dist = (timeDelta * 34300) / 2

        #The estimated time point of the measurement
        measureTime = (start + end) / 2

        latest[self.name]= (measureTime, dist)
        return latest[self.name]


class MovingAverage:
    """MovingAverage is self explanatory"""
    def __init__(self):
        self.data = np.zeros(MASIZE)
        self.idx = 0
        self.n = 0
        self.average = 0.0

    def append(self, pnt):
        if self.n == MASIZE:
            self.average += float(pnt) / MASIZE - self.data[self.idx] / MASIZE
            self.data[self.idx] = float(pnt)
            self.idx += 1
            if self.idx == MASIZE:
                self.idx = 0
        else:
            if self.n > 0:
                self.average -= self.data[self.idx] / self.n
                self.average *= float(self.n) / (self.n + 1)
            self.average += float(pnt) / (self.n + 1)
            self.data[self.idx] = float(pnt)
            self.idx += 1
            self.n += 1
            if self.idx == MASIZE:
                self.idx = 0


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
        threads = [Thread(target=self.sensorList[name].measure, args=())
                        for name in self.sensorList]
        _ = [t.start() for t in threads]
        _ = [t.join() for t in threads]
        for sensor in self.sensorList:
            self.movingAverages[sensor].append(latest[sensor][1])
            if latest[sensor][1] != 0:
                overallMeasure += latest[sensor][1] - self.movingAverages[sensor].average
                overallTime += latest[sensor][0]
                usedSensors += 1
        if usedSensors == 0:
            return (0, 0)
        return (overallTime/usedSensors, overallMeasure/usedSensors)


class SDFT:
    def __init__(self, interpolFunc):
        self.newestMeasureTime = time.time()
        self.newestMeasure = 0
        self.oldestMeasure = 0
        self.interpolFunc = interpolFunc
        self.freqs = np.zeros(DFTSIZE + 1, dtype=np.complex)
        self.measures = np.zeros(DFTSIZE)
        self.coeffs = np.zeros(DFTSIZE, dtype=np.complex)
        self.index = 0
        self.initCoeffs()

    def initCoeffs(self):
        for i in range(DFTSIZE):
            a = -2.0 * np.pi * i / float(DFTSIZE)
            self.coeffs[i] = complex(np.cos(a), np.sin(a))

    def append(self, measure):
        if (measure == (0,0)):
            return False
        interMeasure = self.interpolFunc(self.newestMeasureTime, measure[0],
                                                       self.newestMeasure, measure[1])
        if self.index + 1 == DFTSIZE:
            self.measures[0]  = self.newestMeasure = measure[1]
        else:
            self.measures[self.index + 1]  = self.newestMeasure = measure[1]
        self.newestMeasureTime = measure[0]
        delta = complex(self.newestMeasure - self.measures[self.index])
        ci = 0
        for i in range(DFTSIZE):
            self.freqs[i] += delta * self.coeffs[ci]
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
        for i in range(1000):
            self.iter()
            time.sleep(float(TRIGTIME)/1000)

    def iter(self):
        self.sdft.append(self.sensors.measure())
        #clear()
        #print max([f.real for f in self.sdft.freqs])


if __name__ == "__main__":
    sensors = SensorVector()
    sensors.append('BACK', DistSensor('BACK', 24, 18))
    #sensors.append('FRONT', DistSensor('FRONT', 16, 26))
    hammock = Hammock(sensors)
    hammock.start()




