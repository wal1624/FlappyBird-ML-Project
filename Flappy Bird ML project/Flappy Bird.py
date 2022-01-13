import pygame
import neat
import time
import os
import random

pygame.font.init()

# Constants
WIN_WIDTH = 500
WIN_HEIGHT = 800

GEN = 0

# Flappy's images in an array
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
# Other images
PIPE_IMGS = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMGS = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMGS = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

# Fonts
STAT_FONT = pygame.font.SysFont("comicsans", 50)


class Bird:
    # Constants
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        # Setting all of the initial values
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        # The physics equation for jump arc
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2
        # Terminal Velocity
        if d >= 16:
            d = 16
        # Makes the jump upward faster
        if d < 0:
            d -= 2

        self.y = self.y + d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1
        # Setting the animation images based upon image count
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        # Checking to see if the tilt is less than -80 so it doesn't flap
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2
        # Rotates the image around the center of the bird
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        # For collision purposes: gives us a 2d list of the pixels of an object in the game; in this case,
        # Flappy's pixels
        return pygame.mask.from_surface(self.img)


class Pipe:
    # Constants for the class
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0
        # Keeping a track of where the pipe top and bottoms are going to be drawn
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMGS, False, True)
        self.PIPE_BOTTOM = PIPE_IMGS
        # For collision purposes
        self.passed = False
        self.set_height()

    def set_height(self):
        # Sets the pipe's location randomly
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        # Draws the pipes onto the window
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        # Get all of the masks from each game object
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # Create an offset: how far the masks are from each other
        # From bird to top
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        # From bird to bottom pipe
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Point of collision from bird to the pipes
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True

        return False


class Base:
    # Class constants
    VEL = 5
    WIDTH = BASE_IMGS.get_width()
    IMG = BASE_IMGS

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # Essentially allows the base to move while the second base comes in at the same VEL (Cycles back when it is
        # off of the screen)
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


# Draw the game
def draw_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMGS, (0, -200))

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 20 - text.get_width(), 10))

    text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)

    for bird in birds:
        bird.draw(win)

    pygame.display.update()


# TU the changes we need to make to this main function for the neat algorithm: 7:07:43
def main(genomes, config):
    # Note: Not that efficient
    global GEN
    GEN += 1
    # Keep a track of all of the neuron networks (TU: 7:09:45)
    nets = []
    # Keep a track of all of the genomes (Understand this term better)
    ge = []
    birds = []
    # We have the below for loop structure because genomes is a tuple with the first part being the id and the second
    # part being the genome itself, this is how you loop through tuples
    for _, g in genomes:
        # Essentially, what the below does is for each genome, we create a neural network for it and append that
        # neural network to nets and append that bird who has the genome to birds and finally set fitness to 0,
        # initially, for all genomes and then append the genomes to ge
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(700)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0

    run = True
    # Main game loop
    while run:
        # Sets the framerate to 30 fps (needed to make bird move reasonably)
        # Note, we can make the clock tick faster to allow our model to train much faster
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # At max, there will be two pipes on the screen, and so we need to account for that in our model
        pipe_ind = 0
        if len(birds) > 0:
            # If we pass the first pipe then look at the second pipe or the [1] in the pipes list
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            # So we are going to make the bird jump if the output of the neural network is greater than 0.5 by giving
            # it the offsets and the y's position of the bird
            bird.move()
            # Give it some fitness for surviving, or move forward
            # This for loop is called 30 times per second so in theory we increase fitness points every second
            ge[x].fitness += 0.1

            output = nets[x].activate(
                (bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        # bird.move()
        add_pipe = False
        # removed pipes
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    # If a bird hits a pipe, then remove a fitness
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            pipe.move()

        # Score gets incremented once a pipe is added
        if add_pipe:
            score += 1
            # If a bird goes through a pipe, then increase its fitness score
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(700))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, (GEN - 1))


# main()

def run(config_path):
    # Call in our configuration path by calling all of the subheadings we used in the config text file
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    # Adding in our population
    p = neat.Population(config)

    # See all of the neat statistics of our model
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())

    # ANd boom, like that we have just created our neat algorithm
    # Calls our activision function, main, 50 times
    winner = p.run(main, 50)
    # If we wanted to save the best flappy file, we can pickle it (TU: 7:31:30)


if __name__ == "__main__":
    # Get to the configuration file
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
