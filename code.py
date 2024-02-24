# LoraCWBeacon Copyright 2023 Joeri Van Dooren (ON3URE)

import asyncio

import adafruit_si5351
import board
import busio
import cedargrove_ad5245
import config
import pwmio
from digitalio import DigitalInOut, Direction, Pull

# User config
FREQ = config.FREQ
SIDEFREQ = config.SIDEFREQ

# Const
OFF = 0
ON = 2**15

# Create the I2C interface.
XTAL_FREQ = 25000000
i2c = busio.I2C(scl=board.GP21, sda=board.GP20)
si5351 = adafruit_si5351.SI5351(i2c)

# setup buzzer (set duty cycle to ON to sound)
buzzer = pwmio.PWMOut(board.GP15, variable_frequency=True)
buzzer.frequency = SIDEFREQ

# setup push buttons
rx = DigitalInOut(board.GP25)
rx.direction = Direction.OUTPUT
rx.value = True

# setup push buttons
tx = DigitalInOut(board.GP22)
tx.direction = Direction.OUTPUT
tx.value = False

cwKEY = DigitalInOut(board.GP14)
cwKEY.direction = Direction.INPUT
cwKEY.pull = Pull.UP

tuneUP = DigitalInOut(board.GP8)
tuneUP.direction = Direction.INPUT
tuneUP.pull = Pull.UP

tuneDOWN = DigitalInOut(board.GP7)
tuneDOWN.direction = Direction.INPUT
tuneDOWN.pull = Pull.UP

tuneFUP = DigitalInOut(board.GP10)
tuneFUP.direction = Direction.INPUT
tuneFUP.pull = Pull.UP

tuneFDOWN = DigitalInOut(board.GP9)
tuneFDOWN.direction = Direction.INPUT
tuneFDOWN.pull = Pull.UP

volUP = DigitalInOut(board.GP12)
volUP.direction = Direction.INPUT
volUP.pull = Pull.UP

volDOWN = DigitalInOut(board.GP11)
volDOWN.direction = Direction.INPUT
volDOWN.pull = Pull.UP


def setFrequencyRx(frequency):
    xtalFreq = XTAL_FREQ
    divider = int(900000000 / frequency)
    if divider % 2:
        divider -= 1
    pllFreq = divider * frequency
    mult = int(pllFreq / xtalFreq)
    l = int(pllFreq % xtalFreq)
    f = l
    f *= 1048575
    f /= xtalFreq
    num = int(f)
    denom = 1048575
    si5351.pll_a.configure_fractional(mult, num, denom)
    si5351.clock_0.configure_integer(si5351.pll_a, divider)


def setFrequencyTx(frequency):
    xtalFreq = XTAL_FREQ
    divider = int(900000000 / frequency)
    if divider % 2:
        divider -= 1
    pllFreq = divider * frequency
    mult = int(pllFreq / xtalFreq)
    l = int(pllFreq % xtalFreq)
    f = l
    f *= 1048575
    f /= xtalFreq
    num = int(f)
    denom = 1048575
    si5351.pll_a.configure_fractional(mult, num, denom)
    si5351.clock_1.configure_integer(si5351.pll_a, divider)


async def receiveLoop():
    global FREQ
    setFrequencyTx(1000000)
    setFrequencyRx(FREQ * 1000)
    print("Measured Frequency: {0:0.3f} MHz".format(si5351.clock_0.frequency / 1000000))
    si5351.outputs_enabled = True
    # setFrequencyTx(0)
    # print('Measured Frequency: {0:0.3f} MHz'.format(si5351.clock_1.frequency/1000000))
    ad5245 = cedargrove_ad5245.AD5245(address=0x2C)
    ad5245.wiper = 255
    resetTx = False
    while True:
        await asyncio.sleep(0)
        if volUP.value is False:
            if ad5245.wiper < 230:
                ad5245.wiper = ad5245.wiper + 25
                print(ad5245.wiper)
            await asyncio.sleep(0.15)
        if volDOWN.value is False:
            if ad5245.wiper > 25:
                ad5245.wiper = ad5245.wiper - 25
                print(ad5245.wiper)
            await asyncio.sleep(0.15)
        if tuneDOWN.value is False:
            FREQ = FREQ - 1
            print(FREQ)
            setFrequencyRx(FREQ * 1000)
            print(
                "Measured Frequency: {0:0.3f} MHz".format(
                    si5351.clock_0.frequency / 1000000
                )
            )
            await asyncio.sleep(0.15)
        if tuneUP.value is False:
            FREQ = FREQ + 1
            print(FREQ)
            setFrequencyRx(FREQ * 1000)
            print(
                "Measured Frequency: {0:0.3f} MHz".format(
                    si5351.clock_0.frequency / 1000000
                )
            )
            await asyncio.sleep(0.15)
        if tuneFDOWN.value is False:
            FREQ = FREQ - 0.1
            print(FREQ)
            setFrequencyRx(FREQ * 1000)
            print(
                "Measured Frequency: {0:0.3f} MHz".format(
                    si5351.clock_0.frequency / 1000000
                )
            )
            await asyncio.sleep(0.15)
        if tuneFUP.value is False:
            FREQ = FREQ + 0.1
            print(FREQ)
            setFrequencyRx(FREQ * 1000)
            print(
                "Measured Frequency: {0:0.3f} MHz".format(
                    si5351.clock_0.frequency / 1000000
                )
            )
            await asyncio.sleep(0.15)
        if cwKEY.value is False:
            rx.value = False
            if resetTx is False:
                setFrequencyTx(FREQ * 1000)
                resetTx = True
            print(
                "Measured Frequency: {0:0.3f} MHz".format(
                    si5351.clock_1.frequency / 1000000
                )
            )
            tx.value = True
            buzzer.duty_cycle = ON
            await asyncio.sleep(0)
        if cwKEY.value is True:
            buzzer.duty_cycle = OFF
            tx.value = False
            if resetTx is True:
                setFrequencyTx(1000000)
                resetTx = False
            rx.value = True
            await asyncio.sleep(0)


async def main():
    # loop = asyncio.get_event_loop()
    # loraL = asyncio.create_task(loraLoop())
    cwL = asyncio.create_task(receiveLoop())
    await asyncio.gather(cwL)


asyncio.run(main())
