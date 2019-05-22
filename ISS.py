import threading
import time
import sys
import random
import requests
import numpy as np
import json


def req(*args):
    r = requests.get("http://api.open-notify.org/iss-now.json")
    obj = str(r.json())
    return r


class Server():
    def __init__(self):
        self.lock = threading.Lock()         #locker for general process 
        self.printer = threading.Lock() 
        self.data_lock = threading.Lock()    #locker for specyfic data 
        self.alive = True                    #check server state
        self.data = []                  #initiate array for storing data
        self.time = []                       #for timestamp
        self.flag = True                   #Flag for print last page and turn of printing
        self.bin_time = 1                  # bins will be further use for store place from last print 
        self.bin_data = 1
        self.distance = 0                  # distance will be sum of distances counted during printing, it is more accurate way to count distance on the ball
        
    def start(self, s):
        t = threading.Thread(target=self.run)
        h = threading.Thread(target=self.show_data)
        t.start()
        h.start()
        time.sleep(s)    #running time of server
        print('data release started')
        self.get_data1()
        self.get_data2()
        print('data released')
        self.stop()
#======================================        
    def run(self):
        print("running...")
        
        sleep_peroid = 0.1
        a = str(self.req())
        with self.data_lock:
            self.data.append(a)
            self.time.append(time.time())  
            
        while (self.alive):     #will enter loop onlny when flag is true - server is runninng
            b = str(self.req())
            tb = time.time()
            #print (a, b)
            if (a != b):
                with self.data_lock:
                    self.time.append(tb)
                    self.data.append(b)
                a = b
            time.sleep(sleep_peroid)
                
        print("Server is stoped.")
            
    def stop(self):
        self.alive = False
        print("Server is stopping.")
        
    def get_data1(self):
        with self.data_lock:       # with funciton allows safly envolve the code and then exit like file.close()
            return self.data
    def get_data2(self):
        with self.data_lock:       # with funciton allows safly envolve the code and then exit like file.close()
            return self.time
            
    def show_data(self):
        print ('printing stored data: ')
        counter = 0
        while (self.alive):
            if ( (len(self.data)) > 2 ):
                while (self.flag):
                    print_peroid = (1 + 4*(random.random()) )
                    self.what_to_show(print_peroid)
                    time.sleep(print_peroid)
            else :
                time.sleep(0.1)
                counter +=1
                if (counter > 50):
                    self.alive = False
                    print ('problem 404 occured')
        print ('printing is stopped')
        
    def req(self, *args):
        r = requests.get("http://api.open-notify.org/iss-now.json")
        obj = str(r.json())
        #print(obj)
        return obj
        
#====================================== 
    def what_to_show(self, print_peroid):
    #initiate arrays for data, it can be done also by variables
        data = []
        data_pos = []
    #just collect data using locker safty function   
        with self.data_lock:
            t0 = float(self.time[0])
            t1 = float(self.time[self.bin_time])
            t2 = float(self.time[-1])
            data.append( str(self.data[0]) )     #starting data value, used for average velocity
            data.append( str(self.data[self.bin_data]) )
            data.append( str(self.data[-1]) )
            self.bin_time = len(self.time) - 1 
            self.bin_data = len(self.data) - 1
    
        #print (data[-1])      #if You want to direct check the data use this
    #===covertion===
    # convert string for json
        for i in range (0,len(data)):
            data[i] = self.proper_conv(data[i])
    # convert data to json format
        data0 = json.loads(data[0])    
        data1 = json.loads(data[1])
        data2 = json.loads(data[2])
    #convert inside json format to assemble json dict
        data_pos.append(str(data0["iss_position"]))
        data_pos.append(str(data1["iss_position"]))
        data_pos.append(str(data2["iss_position"]))
        
        for i in range (0, len(data)):
            data_pos[i] = self.proper_conv(data_pos[i])
        
        data_pos0 = json.loads(data_pos[0])
        data_pos1 = json.loads(data_pos[1])
        data_pos2 = json.loads(data_pos[2])  
    #===end of covertion===
    
        #take the data from json and do counting:
        lognitude_change = abs(abs(float(data_pos2["longitude"]))  - abs(float(data_pos1["longitude"])))
        latitude_change = abs(abs(float(data_pos2["latitude"]))  - abs(float(data_pos1["latitude"])))
        Rz = (405 + 6371) #radius of satelite from the center of earth, powerd by wikipiedia
        lognitude_change_km = (lognitude_change/360) *2*np.pi*Rz
        latitude_change_km = (latitude_change/360) *2*np.pi*Rz
        R = (lognitude_change_km**2 + latitude_change_km**2 )**(0.5)  #distance taken
    
        #delta_t = (float(data2["timestamp"])  - float(data1["timestamp"])) / 3600      # method 1 of counting time
        delta_t = (t2 - t1) / 3600 #[h]          method 2 of counting time, more accurate

        if (delta_t == 0):
            delta_t = 1
            print ('======= delta_t soft error ==========')
        
        velocity = R / delta_t   #[km/h] , wikipedia says: 27743.8 km/h
            
        print ( 'longitude change:', lognitude_change )
        print ( 'latitude change:', latitude_change  )
        #print ( 'longitude change [km]:', lognitude_change_km )
        #print ( 'latitude change [km]:', latitude_change_km  )
        print ( 'current velocity [km/h]:', velocity)

        self.distance += R

        if  ( ( (-1)*(timeup + t0) + (time.time() + print_peroid))  > 0 ) :
            
            lognitude_change = abs(abs(float(data_pos2["longitude"]))  - abs(float(data_pos0["longitude"])))
            latitude_change = abs(abs(float(data_pos2["latitude"]))  - abs(float(data_pos0["latitude"])))
            lognitude_change_km = (lognitude_change/360) *2*np.pi*Rz
            latitude_change_km = (latitude_change/360) *2*np.pi*Rz
            delta_t = (t2 - t0) / 3600
            R = self.distance
            velocity = R / delta_t   #[km/h] , wikipedia says: 27743.8 km/h
            
            print ("\n", '========= TOTAL CHANGE OF ISS DURING SIMULATION =========')
            print ( 'time counted [s]:', (t2 - t0 )  )
            print ( 'time refered [s]:', (float(data2["timestamp"])  - float(data0["timestamp"]))  )
            print ( 'total longitude change [deg]:', lognitude_change )
            print ( 'total latitude change [deg]:', latitude_change  )
            print ( 'total longitude change [km]:', lognitude_change_km )
            print ( 'total latitude change [km]:', latitude_change_km  )
            print ( 'distance taken [km]' , R)
            print ( 'average velocity [km/h]:', velocity)
                   
            self.flag = False

    # function that do some operations to fit properly data to json: '' -> "" , [] -> <blank>
    def proper_conv(self, func): 
        func = str(func)
        func = func.replace("'","+")  
        func  = func.replace('+','"')
        func  = func.replace('[','')
        func  = func.replace(']','')
        return func  
    
#======================================  end of class             
    
if (str(req()) == '<Response [200]>'):            
    timeup = 40         #how long server should be turned on ?
    Server().start(timeup)
    time.sleep(1)
    print ('process complete')
else :
    print('please chceck internet connection')
    print(str(req()) )
