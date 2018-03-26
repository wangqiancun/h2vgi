from __future__ import division
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import pdb, traceback, sys
import scipy
from scipy import signal
import numpy as np
import datetime
import cPickle as pickle

dateparse = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
df = pd.read_excel('../data/inputforJosh/cities/DC.xlsx',parse_dates=['datetime'], date_parser=dateparse)

final = df.sort(columns='datetime')
#df = FCEVstatus.loc['2017-03-24']
final.to_excel('sortedoutputDC.xlsx')
