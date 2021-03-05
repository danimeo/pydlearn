from tkinter import Tk, StringVar

from scipy.signal import butter, lfilter
import numpy as np

from dcam_bci_data_processing import data_loop


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

str_var = StringVar(Tk(), '', '')
data_loop(str_var)

# Remove Noise
nsamples = my_data[:, 1].shape[0]
T = nsamples/400
t = np.linspace(0, T, nsamples, endpoint=False)
fs = 400.0
lowcut = 4.0
highcut = 50.0
my_data[:, 2] = butter_bandpass_filter(my_data[:, 2], lowcut, highcut, fs, order=6)
my_data[:, 3] = butter_bandpass_filter(my_data[:, 3], lowcut, highcut, fs, order=6)
my_data[:, 4] = butter_bandpass_filter(my_data[:, 4], lowcut, highcut, fs, order=6)
my_data[:, 5] = butter_bandpass_filter(my_data[:, 5], lowcut, highcut, fs, order=6)

