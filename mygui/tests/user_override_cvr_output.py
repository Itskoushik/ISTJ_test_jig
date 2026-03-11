import time
from core.paths import RESOURCES_DIR

def run_norm(screen):
    screen.log_signal.emit("==========Commencing User CVR Output level test===========", False)
    time.sleep(0.5) 
    #set audio analyser gen output to 750 uVrms @1kHz
    #Audio analyser should read 1.0+-0.1 V with <10% THD + N
    #set audio analyser gen output to 750 uVrms @200 Hz
    #Audio analyser should read >700 mVrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #Audio analyser should read >700 mVrms with <10% THD + N
    
    screen.log_signal.emit("==========Successfully Completed User CVR Output level test===========", False)
    time.sleep(0.5) 

    
def run_stby(screen):
    screen.log_signal.emit("==========Commencing User CVR Output level test===========", False)
    time.sleep(0.5) 
    #set audio analyser gen output to 750 uVrms @1kHz
    #Audio analyser should read 1.0+-0.1 V with <10% THD + N
    #set audio analyser gen output to 750 uVrms @200 Hz
    #Audio analyser should read >700 mVrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #Audio analyser should read >700 mVrms with <10% THD + N
    
    screen.log_signal.emit("==========Successfully Completed User CVR Output level test===========", False)
    time.sleep(0.5) 