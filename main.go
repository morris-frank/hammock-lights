package main

import (
	"fmt"
	"github.com/mjibson/go-dsp/fft"
	"github.com/stianeikeland/go-rpio"
	"os"
	"time"
)

//The used pins
const (
	pinNW = rpio.Pin(0)
	pinNE = rpio.Pin(2)
	pinSW = rpio.Pin(3)
	pinSE = rpio.Pin(4)

	pinTrigger = rpio.Pin(7)
	pinEcho    = rpio.Pin(8)
)

func setup() {
	pinNW.Output()
	pinNE.Output()
	pinSW.Output()
	pinSE.Output()

	pinTrigger.Output()
	pinEcho.Input()
}

func distance() float64 {
	pinTrigger.High()

	//Wait for 10µs
	time.Sleep(time.Microsecond * 10)
	pinTrigger.Low()

	LaunchTime := time.Now()
	ReturnTime := time.Now()

	for pinEcho.Read() == 0 {
		LaunchTime = time.Now()
	}

	for pinEcho.Read() == 1 {
		ReturnTime = time.Now()
	}

	ShotTime := ReturnTime.Sub(LaunchTime)

	//Multiply the elapsed time with the speed of sound and divide by 2 as
	//the shot has to travel back
	distance := (ShotTime.Seconds() * 34300) / 2

	return distance
}

func main() {
	fmt.Printf("Starting hammock-light s...\n")

	// Open and map memory to access gpio, check for errors
	if err := rpio.Open(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	defer rpio.Close()

	pin = rpio.Pin(11)
	pin.Output()

	/*
		setup()

		for i := 0; i < 20; i++ {
			pinNW.Toggle()
			time.Sleep(time.Second * 2)
			pinNE.Toggle()
			time.Sleep(time.Second * 2)
			pinSW.Toggle()
			time.Sleep(time.Second * 2)
			pinSE.Toggle()
			time.Sleep(time.Second * 2)
		}
	*/

}
