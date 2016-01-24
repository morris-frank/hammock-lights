package main

import (
        "fmt"
        "github.com/stianeikeland/go-rpio"
        "os"
        "time"
)

type Pin uint8

//The used pins
const (
  pinNW = rpio.Pin(0)
  pinNE = rpio.Pin(2)
  pinSW = rpio.Pin(3)
  pinSE = rpio.Pin(4)
)

func carousel() {

}

func main() {
	fmt.Printf("Starting hammock-lights...\n")

  // Open and map memory to access gpio, check for errors
  if err := rpio.Open(); err != nil {
    fmt.Println(err)
    os.Exit(1)
  }

   defer rpio.Close()

   pinNW.Output()
   pinNE.Output()
   pinSW.Output()
   pinSE.Output()

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

}
