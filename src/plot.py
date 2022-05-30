import matplotlib.pyplot as plt
import os

class Plot:
    def __init__(self, path, dpi):
        self._path = path
        self._dpi = dpi

    def plot_data(self, data, filename, xlabel, ylabel):
        """
        Produce a plot of performance of the agent over the session and save the relative data to txt
        """
        #min_val = min(data)
        #max_val = max(data)

        # plt.title("Rewards per Episode")

        plt.rcParams.update({'font.size': 12})  # set bigger font size

        plt.plot(data)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        
        #plt.ylim(min_val - 0.05 * abs(min_val), max_val + 0.05 * abs(max_val))
        fig = plt.gcf()

        fig.savefig(os.path.join(self._path, f'plot_{filename}.png'), dpi=self._dpi)
        plt.close("all")

        #Save data to .txt file
        with open(os.path.join(self._path,  f'plot_{filename}_data.txt'), "w") as file:
            for value in data:
                    file.write("%s\n" % value)

    def scatter_plot(self, x, y, filename, xlabel, ylabel):
        plt.scatter(x, y, alpha = 1/5)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        # plt.show()

        fig = plt.gcf()

        fig.savefig(os.path.join(self._path, f'plot_{filename}.png'), dpi=self._dpi)
        plt.close("all")

        #Save data to .txt file
        with open(os.path.join(self._path,  f'plot_{filename}_data.txt'), "w") as file:
            for value in data:
                    file.write("%s\n" % value)
