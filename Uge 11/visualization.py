import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class Visual_interface:
    def __init__(self, screen_shape):
        self.fig, ((self.ax1, self.ax2), (self.ax3,_)) = plt.subplots(2, 2)
        self.bargraph = BarGraph(self.ax1, self.fig)
        self.animation = AnimatedHeatmap(screen_shape, self.ax2, self.fig)
        self.value_loss = LineGraph(self.ax3, self.fig, "value loss")
        self.entropy_loss = LineGraph(self.ax3, self.fig, "entropy loss")
        self.policy_loss = LineGraph(self.ax3, self.fig, " policy loss")
        self.ax3.legend()
        plt.ion()
        plt.show()

    def update(self, screen_data, meta_action_data):

        self.animation.update(screen_data)
        self.bargraph.update(meta_action_data)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def update_full(self, value_loss, entropy_loss, policy_loss):
        self.value_loss.update(value_loss)
        self.policy_loss.update(policy_loss)
        self.entropy_loss.update(entropy_loss)
        self.ax3.relim()
        self.ax3.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


class LineGraph:
    def __init__(self, ax, fig, label):
        self.x = []
        self.y = []

        self.graph, = ax.plot(self.x,self.y, label = label)
    def update(self, data):
        self.y.append(data)
        self.x.append(self.x[-1] + 1 if len(self.x) > 0 else 0)
        self.graph.set_data(self.x, self.y)

class BarGraph:
    def __init__(self, ax, fig):
        x = [
            "select",
            "move",
            "attack",
            "camera",
            "noop",
            "train unit"
        ]
        self.bargraph = ax.bar(x, np.random.rand(len(x)))
        ax.set_xticklabels(x, rotation=-30)
    
    def update(self, data):
        for bar, height in zip(self.bargraph, data):
            bar.set_height(height)

class AnimatedHeatmap:
    def __init__(self, shape, ax, fig):
        self.shape = tuple(shape)
        self.ax = ax
        self.heatmap = self.ax.imshow(np.random.rand(shape[0],shape[1]), cmap='viridis', interpolation='nearest')
        self.cbar = fig.colorbar(self.heatmap, ax=self.ax)

    def update(self, data):
        if(np.shape(data)[0]==1): data = data[0]
        assert np.shape(data) == self.shape, f"data of shape: {np.shape(data)} does not plot of shape: {self.shape}"
        vmin = np.min(data)
        vmax = np.max(data)
        self.heatmap.set_clim(vmin, vmax)
        self.heatmap.set_array(data)
