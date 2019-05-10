parameters = {
  "Default": {
    'DM_low' : 0.,             #Lowest used DM value
    'DM_high' : 100.,          #Highest used DM value
    'DM_search_low' : 5.,      #Lowest DM value to search
    'DM_search_high' : 95.,    #Highest DM value to search
    'SNR_peak_min' : 8.,       #Minumum peak SNR value
    'SNR_min' : 6.,            #Minumum SNR value
    'Downfact_max' : 100,      #Maximum Downfact value
    'FRB_name' : "FRB",
    'down_values' : {50: 2, 150: 3}     #Correct downsample by prepsubband. All DMs above the key value are multiplied by the item value
    },
  
  "FRB121102_Puppi": {
    'DM_low' : 461.,
    'DM_high' : 661.,
    'DM_search_low' : 548.,
    'DM_search_high' : 620.,
    'SNR_peak_min' : 8.,
    'SNR_min' : 6.,
    'Downfact_max' : 300,
    'FRB_name' : "FRB121102",
    },
  
  "FRB130628_Alfa_s0": {
    'DM_low' : 0.,
    'DM_high' : 575.,
    'DM_search_low' : 50.,
    'DM_search_high' : 570.,
    'SNR_peak_min' : 8.,
    'SNR_min' : 5.,
    'Downfact_max' : 300,
    'FRB_name' : "FRB130628",
    'down_values' : {0: 2, 475: 3}
  },

  "FRB130628_Alfa_s1": {
    'DM_low' : 0.,
    'DM_high' : 590.,
    'DM_search_low' : 50.,
    'DM_search_high' : 570.,
    'SNR_peak_min' : 8.,
    'SNR_min' : 5.,
    'Downfact_max' : 300,
    'FRB_name' : "FRB130628",
    'down_values' : {0: 2, 315: 3, 540: 6}
  } 
}
