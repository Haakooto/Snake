from threading import Thread
import time
import numpy as np
from matplotlib.patches import Rectangle, Circle
import matplotlib.pyplot as plt


class Fruit(Circle):
    def __init__(self, pos, radius, ax):
        c = np.asarray([1, 1]) * radius  # placement correction. Is purly visual
        super().__init__(pos + c, radius, fill=True, color="r")
        ax.add_artist(self)
        self.ax = ax

    def eaten(self):  # remove from axes
        for child in self.ax.get_children():
            if isinstance(child, Fruit):
                child.remove()


class Orchard:
    def __init__(self, ax):
        self.snakes = []
        self.ax = ax

        self.timer = 0
        self.delay = 3  # min wait before new fruit
        self.wait = 0.5  # update every this often
        self.pos = np.ones(2) * 2  # somewhere outside canvas
        self.current = None

        self.updater = Thread(target=self.update)  # started from a snake

    def update(self):
        while len(self.snakes) >= 1:  # only run as long as there are snakes
            self.timer += self.wait
            if self.current is None:
                if self.timer >= self.delay:
                    if np.random.uniform() < 0.9:  # 10% chance of placing fruit ever 0.5s 3s after prev was eaten
                        self.add_fruit()
            time.sleep(self.wait)

    def kill(self, snake):  # remove snake from list when it dies
        for s in self.snakes:
            if s == snake:
                self.snakes.remove(s)

    def add_fruit(self):
        N = 1 / self.gridsize
        while True:  # keep sampling positions until one free comes up
            xy = np.random.randint(0, N, size=2)
            xy = xy * self.gridsize
            if self.check_if_open(xy):
                self.pos = xy
                self.current = Fruit(xy, self.gridsize / 2, self.ax)
                return

    def check_if_open(self, xy):
        for snake in self.snakes:
            curr = snake.head
            while curr.next is not None:
                if (xy == curr.xy).all():
                    return False
                curr = curr.next
        return True

    def eaten(self):
        self.current.eaten()
        self.pos = np.ones(2) * 2
        self.current = None
        self.timer = 0


class Joint(Rectangle):
    """
    Class for each joint of snake.
    Works like a linked list, each joint pointing to the next one
    """
    head_pos = []  # head position is used to check for collision later

    def __init__(self, pos, gs, ax, head=False, color="b", idx=0):
        super().__init__(pos, gs*0.95, gs*0.95, fill=True, fc=color)
        # add to axis, so mpl will know to update position when redrawing
        ax.add_artist(self)
        self.next = None
        self.prev = None
        self.set_xy(pos)
        self.ishead = head
        self.idx = idx

        if self.ishead:
            Joint.head_pos.append(self.xy)

    def move(self, new):
        """
        each joint checks if new position is same as new head position
        If i later want to have 2-player, must change way head position is stored
        """
        crash = False
        if self.ishead:
            Joint.head_pos[self.idx] = new
        else:
            for i, snake_head in enumerate(Joint.head_pos):
                if (new == snake_head).all():  # use .all as it is boolean tuple
                    if i != self.idx:
                        Snake.box[i].kill()
                        print("Oh no, you crashed into another snake")
                    else:
                        print("Oh no, you crashed into yourself... Idiot")
                        return True
        if self.next is not None:  # move next before self
            crash = self.next.move(self.xy)
        self.set_xy(new)
        return crash

    def flip(self):
        old = self  # head
        this = old.next

        old.ishead = False
        old.prev = old.next
        old.next = None
        while this.next is not None:
            this.prev = this.next
            this.next = old
            old = this
            this = this.prev

        this.ishead = True
        this.next = old
        this.prev = None

        Joint.head_pos[self.idx] = this.xy
        return this, this.xy, np.sign(np.asarray(this.xy) - np.asarray(old.xy))


class Snake:
    box = []

    def __init__(self, ax, orchard, color="b", dead=False):
        self.ax = ax
        self.dead = dead

        if not self.dead:
            self.orchard = orchard
            self.orchard.snakes.append(self)
            self.idx = len(Snake.box)
            Snake.box.append(self)

            # Start in middle of field in random direction
            self.pos = np.zeros(2) + 0.5
            self.direction = np.asarray([1, 0]) * np.sign(np.random.normal())
            np.random.shuffle(self.direction)

            self.wait = 0.3
            self.dw = 0.001
            self.speed = 0.1
            self.gridsize = self.speed * 0.5
            self.orchard.gridsize = self.gridsize

            self.color = color
            self.head = Joint(self.pos, self.gridsize, ax,
                            head=True, color=self.color, idx=self.idx)

            if len(Snake.box) == 1:
                self.updater = Thread(target=self.update)
                self.updater.start()
                self.orchard.updater.start()

    def update(self):
        # threaded function to keep redrawing every self.wait seconds
        while len(Snake.box) > 0:
            for snake in Snake.box:
                if snake.dead:
                    # print(Joint.head_pos, snake.pos)
                    Snake.box.remove(snake)
                    Joint.head_pos[snake.idx] = np.ones(2) * 2
                    cnt = 0
                    # color snake black when dead
                    curr = snake.head
                    while curr.next is not None:
                        cnt += 1
                        curr.set_color("k")
                        curr = curr.next
                    curr.set_color("k")
                    plt.draw()
                    self.orchard.kill(snake)
                    print("You fucking ded m8")
                    print(f"You ate {cnt} fruits")
                    print()
                else:
                    snake.move()
            plt.draw()
            time.sleep(self.wait)

    def move(self):
        # update position, check for dead snake or eat
        self.pos += self.gridsize * self.direction
        # print(self.pos, self.orchard.pos, (abs(self.pos - self.orchard.pos) < 1e-7).all())
        if (1 < abs(self.pos * 2 - 1)).any():
            print("Oh no, you crashed in the wall")
            self.dead = True
        if self.head.move(self.pos):
            self.dead = True
        if (abs(self.pos - self.orchard.pos) < 1e-7).all():
            self.orchard.eaten()
            self.add_joint()
            self.wait = max(self.dw, self.wait - self.dw)

    def add_joint(self):
        pos = self.pos - self.gridsize * self.direction  # first put right behind head
        new = Joint(pos, self.gridsize, self.ax, color=self.color, idx=self.idx)
        last = self.head
        while last.next is not None:
            last = last.next
        last.next = new  # set aslast joint
        new.prev = last
        # first time moving, will get previous position of (now) second to last joint,
        # so appears as if added to the back, as is intended
        # if joints are later made in different colours, this will look bad

    def turn(self, dir):
        if (self.direction == -dir).all() and self.head.next is not None:
            self.head, self.pos, self.direction = self.head.flip()
        else:
            self.direction = dir

    def kill(self):
        self.dead = True

    def up(self):
        self.turn(np.asarray([0, 1]))

    def down(self):
        self.turn(np.asarray([0, -1]))

    def left(self):
        self.turn(np.asarray([-1, 0]))

    def right(self):
        self.turn(np.asarray([1, 0]))
