import network
from time import sleep, ticks_ms
from umqtt.simple import MQTTClient
from machine import I2C, ADC, Pin
import BME280
from json import dumps
import NAU7802

# Setup I2C and other globals
i2c = I2C(freq=400000, scl=25, sda=26)

def setup_bme():
    # ESP32 - Pin assignment
    bme = BME280.BME280(address=119, i2c=i2c)
    bme.sealevel = 101591.66
    return bme
    
def sense_bme(bme):
#    temp = bme.temperature
 #   hum = bme.humidity
  #  pres = bme.pressure
    temp, pres, hum = bme.values
    alt = bme.altitude
    dew = bme.dew_point
    #print(f"{temp}:{type(temp)}, {pres}:{type(pres)}, {hum}:{type(hum)}")
    # uncomment for temperature in Fahrenheit
    temp = float(temp[:-1]) * (9/5) + 32
    dew = (dew/100) * (9/5) + 32
    alt = alt*3.28084
    return({"Temperature": f"{temp:.2f}", "Pressure": pres, "Humidity": hum, "Dew point": f"{dew:.2f}", "Approximate altitude": f"{alt:.2f}"})

def setup_scale():

    nau7802 = NAU7802.NAU7802(i2c=i2c)
    nau7802.offset = nau7802.get_reading_adv(times=300)
    return nau7802

def  setup_anemometer():
    
    anem = ADC(36)

    #val = adc.read_u16()  # read a raw analog value in the range 0-65535
    
    return anem

def setup_uv_sensor():
    
    uv = ADC(33, atten=ADC.ATTN_0DB)
    
    return uv
wlan = network.WLAN()
wlan.active(True)
wlan.connect("Levi's Asus Wifi 2.4Ghz", "WifiPassword")
while not wlan.isconnected():
    sleep(1)

mqtt = MQTTClient('weather-station', '10.0.0.53', 1883)

while True:
   # try:
    mqtt.connect()
        
    while True:
        bme = setup_bme()
        sense = sense_bme(bme)
        
        nau7802 = setup_scale()
        scale = {'weight': "{:.2f}".format((nau7802.get_reading_adv(times=100) - nau7802.offset)*nau7802.a_sparkfun_500g/10)} # Have to divide by 10 to get close to ounces
        
        anem = setup_anemometer()
        volts = anem.read_uv()/1000000   # read an analog value in microvolts
        voltMin = 0.4
        voltMax = 2.0
        voltRange = voltMax-voltMin
        speedMin = 0
        speedMax = 60
        speedRange = speedMax - speedMin
        
        windSpeed = ((volts-voltMin)/voltRange)*speedRange # in m/s
        
        if windSpeed < 0:
            anemResults = {'windspeed':f"0.00 m/s"}
            
        else:
            anemResults = {'windspeed':f"{windSpeed:.2f} m/s"}
            
        uv = setup_uv_sensor()
        volts = uv.read_uv()/1000000
        
        uvIndex = volts/0.1
        
        uvResults = {'UV Index': f'{uvIndex:.2f}'}
        
        output = sense | scale | anemResults | uvResults
        mqtt.publish('weather', dumps(output), True)
        sleep(1)

            
#    except Exception as e:
 #       print(e)
  #      sleep(10)
  
    
    
