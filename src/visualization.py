import matplotlib.pyplot as plt
import os

class Visualization:
    def __init__(self, folder, dpi):
        self._folder = folder
        self._dpi = dpi
    #def __init__(self, dpi):
        #self._dpi = dpi

    def save_data_and_plot(self, data, filename, xlabel, ylabel):
        """
        Produce a plot of performance of the agent over the session and save the relative data to txt
        """
        #min_val = min(data)
        #max_val = max(data)

        plt.title("Rewards per Episode")

        plt.rcParams.update({'font.size': 12})  # set bigger font size

        plt.plot(data)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        
        #plt.ylim(min_val - 0.05 * abs(min_val), max_val + 0.05 * abs(max_val))
        fig = plt.gcf()

        if not os.path.exists(self._folder):
            os.makedirs(self._folder)

        fig.savefig(f'{self._folder}/plot_{filename}.png', dpi=self._dpi)
        
        #plt.close("all")

        """ with open(os.path.join(self._path, 'plot_'+filename + '_data.txt'), "w") as file:
            for value in data:
                    file.write("%s\n" % value) """