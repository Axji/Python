from urllib import request
import configparser
from global_lib import *

config = configparser.ConfigParser()
config.read('config.ini')

opener = request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

wetterStationen = ['SIO', 'BER', 'BAS', 'CHM', 'CHD', 'GSB',
                   'DAV', 'ENG', 'GVE', 'LUG', 'PAY', 'SIA',
                   'SAE', 'SMA']

cfgBaseUrl = config['DEFAULT']['baseUrl']
cfgstringToReplaceInUrl = config['DEFAULT']['stringToReplaceInUrl']
cfgsleepTimeBetweenFiles = int(config['DEFAULT']['sleepTimeBetweenFiles'])

print(cfgBaseUrl)

DateStart = GlobalLib.date_iso()
    #datetime.datetime.now().isoformat().replace('.', '_').replace(':', '')

for wetterstation in wetterStationen:
    #actualUrl =
    response = opener.open(cfgBaseUrl.replace(cfgstringToReplaceInUrl, wetterstation))
    # print(response.read())
    f = open('daten\\'+DateStart+'_'+wetterstation+'.txt', 'w')
    f.write(response.read().decode("utf-8"))
    time.sleep(cfgsleepTimeBetweenFiles)






#page = request.urlopen("http://www.meteoschweiz.admin.ch/product/output/climate-data/homogenous-monthly-data-processing/data/homog_mo_SIO.txt").read()
#page = request.urlopen("http://www.meteoschweiz.admin.ch/product/output/climate-data/homogenous-monthly-data-processing/data/homog_mo_BER.txt").read()
#page = request.urlopen("http://www.google.com").read()



#from os import walk
#dir = 'C:\\Users\\azen\\Documents\\WetterDaten'


#f = []
#for (dirpath, dirnames, filenames) in walk(dir):
#    f.extend(filenames)
#    break


#print(page)


