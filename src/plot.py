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
       
        fig = plt.gcf()
        plt.show()
        fig.savefig(os.path.join(self._path, f'plot_{filename}.png'), dpi=self._dpi)
        plt.close("all")

        #Save data to .txt file
        #with open(os.path.join(self._path,  f'plot_{filename}_data.txt'), "w") as file:
            #for value in data:
                    #file.write("%s\n" % value)

    def compare_plot(self, filename, x1, y1, x2, y2, xlabel, ylabel):
        plt.scatter(x1, y1, c='b', alpha = 1/5)
        plt.scatter(x2, y2, c='r', alpha = 1/5)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)

        fig = plt.gcf()
        plt.show()
        fig.savefig(os.path.join(self._path, f'plot_{filename}.png'), dpi=self._dpi)

#x1 = [5,7,8,7,2,17,2,9,4,11,12,9,6] #random sample data
#y1 = [99,86,87,88,111,86,103,87,94,78,77,85,86] #random sample data

#x2 = [1,2,8,7,2,17,2,9,4,11,12,9,6,23,12,1,2,3,53,6,5,3,3,4] #random sample data
#y2 = [5,7,8,7,2,17,2,9,4,11,12,9,6,32,12,45,2,1,2,3,1,2,3,1] #random sample data

#test = Plot('sumo_files/plots/', 100) # Plot instance
#test.scatter_plot(x1, y1, 'test', 'the x axis', 'the y axis') #testing scatter plot (one scatter plot)
#test.compare_plot('compare', x1,y1,x2,y2,'the x axis', 'the y axis') #testing compare plot (two scatter plots)



