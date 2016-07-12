import configparser
config = configparser.ConfigParser()

#config['BaseUrl'] = 'http://www.meteoschweiz.admin.ch/product/output/climate-data/' \
#                    'homogenous-monthly-data-processing/data/homog_mo_XXX.txt'

config['DEFAULT'] = {'BaseUrl': 'http://www.meteoschweiz.admin.ch/product/output/climate-data/'
                                'homogenous-monthly-data-processing/data/homog_mo_XXX.txt',
                     'sleep': '3'}
config['global'] = {}
config['global']['Author'] = 'Axel "Axji" Zenklusen'
with open('config.ini', 'w') as configfile:
    config.write(configfile)