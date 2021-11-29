import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from snake import Snake, Orchard
import sys


def key_press_event(event):
    if event.key == "q":
        snake.kill()
        serpent.kill()
        plt.close(fig)
    if event.key == "r":
        print("Responsive")
    if event.key == "g":
        # reserved for testing
        pass
    if event.key == "j":
        # reserved for testing
        pass
    if event.key == "up":
        snake.up()
    elif event.key == "down":
        snake.down()
    elif event.key == "left":
        snake.left()
    elif event.key == "right":
        snake.right()
    if event.key == "w":
        serpent.up()
    elif event.key == "s":
        serpent.down()
    elif event.key == "a":
        serpent.left()
    elif event.key == "d":
        serpent.right()


fig, ax = plt.subplots()
ax.axis("off")
ax.add_artist(Rectangle((0, 0), 1, 1, fill=False, lw=5, ec="k"))


orchard = Orchard(ax)
snake = Snake(ax, orchard, color="b")
if len(sys.argv) > 1:
    serpent = Snake(ax, orchard, color="g")
serpent = Snake(ax, orchard, dead=True)

plt.subplots_adjust(left=0.01,
                    bottom=0.01,
                    right=0.99,
                    top=0.99,
                    wspace=0.1,
                    hspace=0.1)

fig.canvas.callbacks.callbacks = {}
fig.canvas.mpl_connect("key_press_event", key_press_event)

plt.show()
