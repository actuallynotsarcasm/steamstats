import pandas as pd
from matplotlib import pyplot as plt

df = pd.read_csv('speed_data.csv', header=None)
df.columns = ['requests', 'time']
df = df.drop_duplicates('time')
speed = df['requests'][1:].reset_index(drop=True) - df['requests'][:-1].reset_index(drop=True)
speed_over_time = pd.DataFrame({'speed': speed.rolling(window=50).mean(), 'time': df['time'].iloc[1:].reset_index(drop=True)})

fig, axs = plt.subplots(2, 1)
axs[0].plot(df['time'], df['requests'])
axs[0].set_title('Requests over time')
axs[1].plot(speed_over_time['time'], speed_over_time['speed'], color='red')
axs[1].set_title('RPS over time')
plt.show()