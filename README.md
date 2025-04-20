# RP2040-based external monitor for a Linux-based host

Main purpose - stream metrics from a Linux host to a Raspberry Pi Pico (RP2040) and show them on an OLED display.

## Hardware

- Microcontroller - RP2040-Zero by Waveshare (Pico-like MCU board based on Raspberry Pi RP2040)  
- SSD1306‑compatible 0.96" OLED (e.g., GME12864 128×64 I²C)  

### Wiring

- Pico GP0 (I2C0 SDA) → OLED SDA  
- Pico GP1 (I2C0 SCL) → OLED SCL  
- Pico 3V3 → OLED VCC  
- Pico GND → OLED GND  


