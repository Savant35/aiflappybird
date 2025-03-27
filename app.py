import pygame
import neat
import os
import random
import sys
import pickle
pygame.font.init()

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 800
GENERATION = 0
GAME_MODE = "ai" #default game mode
VISUALIZE_AI = False

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
        self.decision: float = 0

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
        if (GAME_MODE == "ai" or GAME_MODE == "trained") and VISUALIZE_AI and hasattr(bird, "decision"):

            # --- Visualize the pipes being "seen" by the bird ---
            # Find the nearest pipe (the first one whose right edge is ahead of the bird)
            nearest_pipe = None
            for pipe in pipes:
                if pipe.x + pipe.PIPE_TOP.get_width() > bird.x:
                    nearest_pipe = pipe
                    break
            if nearest_pipe is not None:
                # Calculate the bird's center position
                bird_center = (bird.x + bird.img.get_width() // 2, bird.y + bird.img.get_height() // 2)
                # Define the key points in the pipe gap
                top_gap = (nearest_pipe.x + nearest_pipe.PIPE_TOP.get_width() // 2, nearest_pipe.height)
                bottom_gap = (nearest_pipe.x + nearest_pipe.PIPE_BOTTOM.get_width() // 2, nearest_pipe.bottom)
                # Draw lines from the bird to the top (red) and bottom (green) of the gap
                pygame.draw.line(win, (255, 0, 0), bird_center, top_gap, 2)
                pygame.draw.line(win, (0, 255, 0), bird_center, bottom_gap, 2)
            
            # --- Visualize the AI decision ---
            # Position the decision arrow just in front of the bird
            start_x = bird.x + bird.img.get_width() + 5
            start_y = bird.y + bird.img.get_height() // 2

            # Treat decision values between 0.4 and 0.6 as "straight" (i.e. effective decision 0.5)
            effective_decision = bird.decision
            if 0.3 <= bird.decision <= 0.6:
                effective_decision = 0.5

            # Map decision to a vertical offset
            scale_factor = 80  # Adjust to set maximum vertical deviation
            offset = (effective_decision - 0.5) * -scale_factor  # negative: higher decision => upward
            target_y = start_y + offset

            arrow_length = 20
            if effective_decision == 0.5:
                # Draw horizontal arrow when going straight
                end_x = start_x + arrow_length
                end_y = start_y
            else:
                # Otherwise, arrow goes vertically to the computed target
                end_x = start_x
                end_y = target_y

            # Draw the decision arrow line (yellow)
            pygame.draw.line(win, (255, 255, 0), (start_x, start_y), (end_x, end_y), 3)

            # Draw an arrow head based on arrow direction
            if effective_decision == 0.5:
                # Horizontal arrow head (pointing right)
                pygame.draw.polygon(win, (255, 255, 0), [
                    (end_x, end_y),
                    (end_x - 5, end_y - 5),
                    (end_x - 5, end_y + 5)
                ])
            else:
                if end_y < start_y:
                    # Arrow pointing upward
                    pygame.draw.polygon(win, (255, 255, 0), [
                        (end_x, end_y),
                        (end_x - 5, end_y + 5),
                        (end_x + 5, end_y + 5)
                    ])
                else:
                    # Arrow pointing downward
                    pygame.draw.polygon(win, (255, 255, 0), [
                        (end_x, end_y),
                        (end_x - 5, end_y - 5),
                        (end_x + 5, end_y - 5)
                    ])

    pygame.display.update()

def run(config_path):
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     config_path)

    p = neat.Population(config)
    #p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(stats)
    winner = None



    try:
        winner = p.run(main, 50)
    except KeyboardInterrupt:
        print("Training interrupted.")
    finally:
        # Retrieve the best genome from each generation
        best_list = stats.best_genomes(-1)

        # Initialize best_all_time to None so it is always defined
        best_all_time = None

        
# Decide which genome to save
        chosen_to_save = None

        if best_all_time is not None and winner is not None:
            if best_all_time.fitness > winner.fitness:
                chosen_to_save = best_all_time
            else:
                chosen_to_save = winner
        elif best_all_time is not None:
            chosen_to_save = best_all_time
        else:
            chosen_to_save = winner

# Check if a saved genome already exists and only overwrite if the new one is better.
        if os.path.exists("best_ai.pkl"):
            with open("best_ai.pkl", "rb") as f:
                saved_genome = pickle.load(f)
            if saved_genome is not None and hasattr(saved_genome, "fitness"):
                if chosen_to_save is not None and chosen_to_save.fitness > saved_genome.fitness:
                    with open("best_ai.pkl", "wb") as f:
                        pickle.dump(chosen_to_save, f)
                    print(f"Saved new best genome with fitness {chosen_to_save.fitness:.2f} to best_ai.pkl")
                else:
                    print(f"Saved genome remains with fitness {saved_genome.fitness:.2f}; not overwriting.")
            else:
                # If for some reason the saved genome is None, save chosen_to_save.
                if chosen_to_save is not None:
                    with open("best_ai.pkl", "wb") as f:
                        pickle.dump(chosen_to_save, f)
                    print(f"Saved best genome with fitness {chosen_to_save.fitness:.2f} to best_ai.pkl")
                else:
                    print("No winner found; not saving any genome.")
        else:
            if chosen_to_save is not None:
                with open("best_ai.pkl", "wb") as f:
                    pickle.dump(chosen_to_save, f)
                print(f"Saved best genome with fitness {chosen_to_save.fitness:.2f} to best_ai.pkl")
            else:
                print("No winner found; not saving any genome.")


 #A standard version of Flappy Bird where the user can control the bird with the spacebar.
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

def trained_game(config_path):
    import pickle

    # Load the best AI genome from file
    with open("best_ai.pkl", "rb") as f:
        winner_genome = pickle.load(f)

    # Create a NEAT config and network from the trained genome
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )
    net = neat.nn.FeedForwardNetwork.create(winner_genome, config)

    # Set up a single Bird, Base, and a Pipe
    bird = Bird(230, 350)
    base = Base(730)
    pipes = [Pipe(700)]
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    run = True

    while run:
        clock.tick(0)  # Control frame rate if desired
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()

        bird.move()

        # Decide which pipe to use for the inputs
        pipe_ind = 0
        if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_ind = 1

        # Network output => single output neuron
        output = net.activate((
            bird.y,
            abs(bird.y - pipes[pipe_ind].height),
            abs(bird.y - pipes[pipe_ind].bottom)
        ))
        bird.decision = output[0]

        # If output is > 0.5, the bird jumps
        if output[0] > 0.5:
            bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            pipe.move()

            # If bird hits a pipe, end run
            if pipe.collide(bird):
                run = False

            # Track if pipe is off screen
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            # Once the bird passes the pipe, mark it for pipe creation
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

        if add_pipe:
            score += 1
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        # If bird goes above the screen or below the base
        if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
            run = False

        base.move()
        draw_window(win, [bird], pipes, base, score, 0)

    pygame.quit()
    sys.exit()


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
            bird.decision = output[0]

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

        #when looking for a champioon
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

#remove later
        TARGET_SCORE = 400  # Set your desired target score here
        best_fitness = max((g.fitness for g in ge), default=0)
        if best_fitness >= TARGET_SCORE:
            print(f"Target score reached: {best_fitness:.2f}. Ending generation early.")
            run = False



if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")

    if len(sys.argv) > 1:
        arg1 = sys.argv[1].lower()
        if arg1 == "play":
            GAME_MODE = "play"
            play_game()
        elif arg1 == "ai":
            GAME_MODE = "ai"
            if len(sys.argv) > 2 and sys.argv[2].lower() == "-v":
                VISUALIZE_AI = True
            run(config_path)
        elif arg1 == "trained":
            GAME_MODE = "trained"
            if len(sys.argv) > 2 and sys.argv[2].lower() == "-v":
                VISUALIZE_AI = True
            trained_game(config_path)
        else:
            print("Usage: python3 app.py [play | ai [-v] | trained]")
    else:
        GAME_MODE = "ai"
        run(config_path)


