#!/usr/bin/python3                                                                                                      
                                                                                                                        
from kafka import KafkaProducer                                                                                         
from random import randint                                                                                              
from time import sleep                                                                                                  
import sys                                                                                                              
                                                                                                                        
BROKER = 'localhost:9092'                                                                                               
TOPIC = 'tweets'                                                                                                      
                                                                                                                        
WORD_FILE = '/usr/share/dict/words'                                                                                     
WORDS = open(WORD_FILE).read().splitlines()                                                                             
                                                                                                                        
try:                                                                                                                    
    p = KafkaProducer(bootstrap_servers=BROKER)                                                                         
except Exception as e:                                                                                                  
    print(f"ERROR --> {e}")                                                                                             
    sys.exit(1)                                                                                                        
                                                                                                                        
while True:                                                                                                             
    message = ''                                                                                                        
    for _ in range(randint(2, 7)):                                                                                      
        message += WORDS[randint(0, len(WORDS)-1)] + ' '                                                                
    print(f">>> '{message}'")                                                                                           
    p.send(TOPIC, bytes(message, encoding="utf8"))                                                                      
    sleep(randint(1,4))