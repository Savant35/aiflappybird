import pygame
import neat
import time
import os
import random
import sys
pygame.font.init()

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 800
GENERATION = 0
GAME_MODE = "ai" #default game mode

#loads all the bird images into a list
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]

#load Pipe image
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png"))) 
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png"))) 
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png"))) 
STAT_FONT = pygame.font.SysFont("comicsans",50)
#POINT_SOUND = pygame.mixer.Sound(os.path.join("imgs", "point.wav"))

def load_high_score():
    if os.path.exists("highscore.txt"):
        with open("highscore.txt", "r") as f:
            try:
                return int(f.read().strip())
            except:
                return 0
    return 0

def save_high_score(score):
    with open("highscore.txt", "w") as f:
        f.write(str(score))

HIGH_SCORE = load_high_score()


#bird class represents bird object moving
class Bird:
    IMGS = BIRD_IMGS
    MAX_Rotation = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x, self.y, self.height = x, y, y
        self.tilt = self.tick_count = self.vel = self.img_count = 0
        self.img = self.IMGS[0]

    #controls when the bird jumps or flaps to go up
    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        tc = self.tick_count
        d = self.vel * tc + 1.5 * (tc * tc)
        d = 16 if d >= 16 else (d - 2 if d < 0 else d)
        self.y += d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_Rotation:
                self.tilt = self.MAX_Rotation
        else:
            self.tilt = max(self.tilt - self.ROT_VEL, -90)

    def draw(self, win):
        self.img_count += 1
        if self.tilt <= -90:
            self.img, self.img_count = self.IMGS[1], self.ANIMATION_TIME * 2
        else:
            frames = [self.IMGS[0], self.IMGS[1], self.IMGS[2], self.IMGS[1]]
            self.img = frames[(self.img_count // self.ANIMATION_TIME) % 4]
            self.img_count %= self.ANIMATION_TIME * 4

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
            return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200  # space between pipes
    VEL = 5    # pipe movement speed

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        # Precompute masks for collision detection.
        self.top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        self.bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        return (bird_mask.overlap(self.top_mask, top_offset) or 
                bird_mask.overlap(self.bottom_mask, bottom_offset)) is not None


class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        w = self.WIDTH  # cache width locally

        if self.x1 + w < 0:
            self.x1 = self.x2 + w
        if self.x2 + w < 0:
            self.x2 = self.x1 + w

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, generation):
    global HIGH_SCORE
    if HIGH_SCORE < score:
        HIGH_SCORE = score
    win.blit(BG_IMG, (0, 0))
    
    for pipe in pipes:
        pipe.draw(win)
    
    score_text = STAT_FONT.render(f"Score: {score}", True, (255, 255, 255))

    if GAME_MODE == "play":
        gen_text = STAT_FONT.render(f"Best: {HIGH_SCORE}", True, (255, 255, 255))
        win.blit(score_text, (WINDOW_WIDTH - 10 - score_text.get_width(), 10))
        win.blit(gen_text, (10, 10))
    else:
        gen_text = STAT_FONT.render(f"Gen: {generation}", True, (255, 255, 255))
        survivors_text = STAT_FONT.render(f"Survivors: {len(birds)}", True, (255, 255, 255))
        win.blit(score_text, (WINDOW_WIDTH - 10 - score_text.get_width(), 10))
        win.blit(gen_text, (10, 10))
        win.blit(survivors_text, (10, 50))    
    base.draw(win)
    
    for bird in birds:
        bird.draw(win)
    
    pygame.display.update()


def main(genomes,config):
    global GENERATION
    GENERATION += 1
    nets = []
    ge = []
    birds = [] 

    for __, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230,350))
        g.fitness = 0
        ge.append(g)

    score = 0
    base = Base(730)
    pipes = [Pipe(700)]
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    run = True
    while run:
        clock.tick(0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()


        pipe_ind = 0
        if len(birds) > 0:
             if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                 pipe_ind = 1
        else:
            run = False
            break


        for x, bird in enumerate(birds):  # give each bird a fitness of 0.1 for each frame it stays alive
            bird.move()
            ge[x].fitness += 0.1
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()


        #bird.move()
        
        add_pipe = False
        rem = []
        for pipe in pipes:
            if birds and not pipe.passed and pipe.x < birds[0].x:
                pipe.passed = True
                add_pipe = True
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        for i in reversed(range(len(birds))):
            if any(pipe.collide(birds[i]) for pipe in pipes):
                ge[i].fitness -= 1
                birds.pop(i)
                nets.pop(i)
                ge.pop(i)

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y +bird.img.get_height()>= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds,pipes, base,score, GENERATION)

def run(config_path):
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     config_path)

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winnder = p.run(main,50) #how many generations i am going to run

#    A standard version of Flappy Bird where the user can control the bird with the spacebar.
def play_game():
    global HIGH_SCORE
    while True:
        bird = Bird(230, 350)
        base = Base(730)
        pipes = [Pipe(700)]
        
        win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        clock = pygame.time.Clock()
        run = True
        score = 0

        while run:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        bird.jump()

            bird.move()

            add_pipe = False
            rem = []
            for pipe in pipes:
                pipe.move()
                if pipe.collide(bird):
                    run = False
                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    rem.append(pipe)
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if add_pipe:
                score += 1
                pipes.append(Pipe(600))

            for r in rem:
                pipes.remove(r)

            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                run = False

            base.move()
            draw_window(win, [bird], pipes, base, score, 0)

        if score > HIGH_SCORE:
            HIGH_SCORE = score
            save_high_score(HIGH_SCORE)

    #pygame.quit()
    #sys.exit()

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")

    if len(sys.argv) > 1 and sys.argv[1].lower() == "play":
        GAME_MODE = "play"
        play_game()
    else:
        run(config_path)
    #run(config_path)


