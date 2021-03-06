import pygame
import numpy as np
import colorsys
from PyEvolv.assets.font import FONT, get_font
from typing import Dict, List, Tuple

def display_creature(f):
    def inner(self, gameDisplay: pygame.Surface, creatures: List) -> None:
        pixels_per_relative = self.display_height / self.relatives_on_screen

        for creature in creatures:
            type, x, y, color, food_color, size, rotation, sensor_1, sensor_2, sensor_3 = creature()
            if self.relative_x <= x <= self.relative_x + self.relatives_on_screen and self.relative_y <= y <= self.relative_y + self.relatives_on_screen:
                size = int(size*pixels_per_relative)
                surf_size = max(size, int(self.constants["max_sensor_length"]*pixels_per_relative))

                creature_surf = pygame.Surface((2*surf_size, 2*surf_size), pygame.SRCALPHA)
                creature_surf = creature_surf.convert_alpha()

                color = tuple(round(i * 255) for i in colorsys.hsv_to_rgb(color[0], color[1], color[2]))
                food_color = tuple(round(i * 255) for i in colorsys.hsv_to_rgb(food_color[0], food_color[1], food_color[2]))

                f(creature_surf, color, food_color, size, surf_size)

                pygame.draw.line(creature_surf, (0,0,0), (surf_size, surf_size),
                                 (int(surf_size + (pixels_per_relative * sensor_1[0] * np.cos(np.radians(sensor_1[1])))),
                                 int(surf_size + (pixels_per_relative * sensor_1[0] * np.sin(np.radians(sensor_1[1])))))
                                )
                pygame.draw.line(creature_surf, (0,0,0), (surf_size, surf_size),
                                 (int(surf_size + (pixels_per_relative * sensor_2[0] * np.cos(np.radians(sensor_2[1])))),
                                 int(surf_size + (pixels_per_relative * sensor_2[0] * np.sin(np.radians(sensor_2[1])))))
                                )
                pygame.draw.line(creature_surf, (0,0,0), (surf_size, surf_size),
                                 (int(surf_size + (pixels_per_relative * sensor_3[0] * np.cos(np.radians(sensor_3[1])))),
                                 int(surf_size + (pixels_per_relative * sensor_3[0] * np.sin(np.radians(sensor_3[1])))))
                                )

                creature_surf = pygame.transform.rotate(creature_surf, rotation)

                dest_x = int(((x-self.relative_x)*pixels_per_relative) - (creature_surf.get_rect().width/2))
                dest_y = int(((y-self.relative_y)*pixels_per_relative) - (creature_surf.get_rect().height/2))

                gameDisplay.blit(creature_surf, (dest_x, dest_y))
    return inner


class Game:
    def __init__(self,display_width:int, display_height:int, y:int, grid:np.ndarray, relatives_on_screen:int, constants:Dict) -> None: # TODO: add primary color and secondary color, ..
        self.display_width = display_width
        self.display_height = display_height
        self.relative_x = 0
        self.relative_y = 0
        self.grid = grid
        self.constants = constants
        self.relative_x_change = 0
        self.relative_y_change = 0
        self.relatives_on_screen = relatives_on_screen
        self.y = y

        pygame.init()

        pygame.font.init()
        self.myfont = FONT

        self.clock = pygame.time.Clock()

        self.surf = pygame.Surface((display_width,display_height))
        pygame.display.set_caption('Evolution Simulator')

        self.sidebar_width = display_width-display_height
        self.map_surf = pygame.Surface((display_height, display_height))
        self.sidebar_surf = pygame.Surface((self.sidebar_width, display_height))
        self.step = 0
        self.creature_info = None

    def next_frame(self, herbivores:List, carnivores:List, creature_counts:Dict[int, int], creature_locs:Dict) -> None:
        self.step += self.constants["evo_steps_per_frame"]

        self.sidebar_surf.fill((255, 255, 255))
        self.map_surf.fill((0,0,0))

        self._display_grid(self.map_surf)
        self._display_herbivores(self.map_surf, herbivores)
        self._display_carnivores(self.map_surf, carnivores)
        self._display_sidebar(self.sidebar_surf, len(herbivores), len(carnivores), creature_counts)
        self._display_info(creature_locs)

        self.surf.blit(self.map_surf, (self.sidebar_width, 0))
        self.surf.blit(self.sidebar_surf, (0, 0))

        self.relative_x = min(max(0, self.relative_x + self.relative_x_change), 10*self.grid.shape[0] - self.relatives_on_screen)
        self.relative_y = min(max(0, self.relative_y + self.relative_y_change), 10*self.grid.shape[1] - self.relatives_on_screen)


    def controller(self, event:pygame.event, creature_locs: Dict) -> None:
        self._grid_controller(event, creature_locs)

    def update_grid(self, new_grid:np.ndarray) -> None:
        assert new_grid.shape == self.grid.shape
        self.grid = new_grid 

    def _grid_controller(self, event:pygame.event, creature_locs:Dict) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.relative_x_change = -3
            elif event.key == pygame.K_RIGHT:
                self.relative_x_change = 3
            
            if event.key == pygame.K_DOWN:
                self.relative_y_change = 3
        
            elif event.key == pygame.K_UP:
                self.relative_y_change = -3

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                self.relative_x_change = 0
            if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                self.relative_y_change = 0
    
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                locs_arr = np.asarray(list(creature_locs.values()))
                relatives_per_pixel = self.relatives_on_screen / self.display_height
                relative_mouse_x = self.relative_x + (int(event.pos[0]) - self.sidebar_width) * relatives_per_pixel
                relative_mouse_y = self.relative_y + (int(event.pos[1]) - self.y) * relatives_per_pixel
                creature_infos = np.where((relative_mouse_x < locs_arr[:, 0] + 10 * relatives_per_pixel)
                                        & (relative_mouse_x > locs_arr[:, 0] - 10 * relatives_per_pixel)
                                        & (relative_mouse_y < locs_arr[:, 1] + 10 * relatives_per_pixel)
                                        & (relative_mouse_y > locs_arr[:, 1] - 10 * relatives_per_pixel))
                if len(creature_infos[0]) == 0:
                    self.creature_info = None
                elif len(creature_infos[0]) > 0:
                    self.creature_info = list(creature_locs.keys())[creature_infos[0][0]]

            if event.button == 4:
                self.relatives_on_screen = min(max(10, self.relatives_on_screen + 3), self.grid.shape[0]*10)
            elif event.button == 5:
                self.relatives_on_screen = min(max(10, self.relatives_on_screen - 3), self.grid.shape[0]*10)

    def _display_grid(self, gameDisplay:pygame.Surface) -> None:
        pixels_per_relative = self.display_height / self.relatives_on_screen
        for x in range(self.grid.shape[0]):
            for y in range(self.grid.shape[1]):
                if self.relative_x <= (x+1)*10 <= self.relative_x + self.relatives_on_screen + 10 and self.relative_y <= (y+1)*10 <= self.relative_y + self.relatives_on_screen + 10:
                    color = self.grid[x, y] 
                    color = np.asarray(colorsys.hsv_to_rgb(color[0], color[1], color[2]))*255
                    pygame.draw.rect(gameDisplay, color, (x*10*pixels_per_relative - self.relative_x*pixels_per_relative, y*10*pixels_per_relative - self.relative_y*pixels_per_relative, pixels_per_relative*10, pixels_per_relative*10))
    
    @display_creature
    def _display_herbivores(creature_surf: pygame.Surface, color:List[int], food_color:List[int], size:int, surf_size:int) -> None:
        pygame.draw.circle(creature_surf, color, (surf_size, surf_size), size)
        pygame.draw.circle(creature_surf, (0,0,0), (surf_size, surf_size), size, min(size, 2))
        pygame.draw.circle(creature_surf, food_color, (surf_size+size//2, surf_size), size//2)


    @display_creature
    def _display_carnivores(creature_surf: pygame.Surface, color:List[int], food_color:List[int], size:int, surf_size:int) -> None:
        pygame.draw.rect(creature_surf, color, (surf_size-size, surf_size-size, size*2, size*2))
        pygame.draw.circle(creature_surf, food_color, (surf_size, surf_size-size//2), size//2)

                
    

    def _display_sidebar(self, gameDisplay: pygame.Surface, n_herbivores: int, n_carnivores: int, creature_counts: Dict[int, int]) -> None:
        if self.creature_info == None:
            herb_pop_size = self.myfont.render("Herbivores: " + str(n_herbivores), False, (0,0,0))
            carn_pop_size = self.myfont.render("Carnivores: " + str(n_carnivores), False, (0,0,0))
            step = self.myfont.render("Step: "+str(self.step), False, (0,0,0))
            gameDisplay.blit(herb_pop_size, (20, 20))
            gameDisplay.blit(carn_pop_size, (20, 60))
            gameDisplay.blit(step, (20, 100))

            n_creatures = n_herbivores + n_carnivores
            current_y = 140
            for i in creature_counts.values():
                count = i[0]
                color = i[1]
                pixels = (self.display_height-160) * (count/n_creatures)
                pygame.draw.rect(gameDisplay,  tuple(round(i * 255) for i in colorsys.hsv_to_rgb(color[0], color[1], color[2])),
                                (20, current_y, self.sidebar_width-40, pixels))
                current_y += pixels

        else:
            species = self.myfont.render("Species: " + str(self.creature_info.species), False, (0,0,0))
            gameDisplay.blit(species, (20, 20))
            net_in = self.creature_info.net.inputs
            net_out = self.creature_info.net.out
            font_size = int((self.display_height - 80) / len(net_in))
            font = get_font(font_size)
            for i, val in enumerate(net_in):
                val_txt = font.render(str(np.around(val, 2)), False, (255,255,255))
                val_txt_dest_x = ((self.sidebar_width-60)/4+20) - val_txt.get_rect().width / 2
                pygame.draw.rect(gameDisplay, (0,0,0), (20, 60 + i*font_size, (self.sidebar_width-60)/2, font_size+2))
                gameDisplay.blit(val_txt, (val_txt_dest_x, 60 + i*font_size))

            out_beginning_y = int(((self.display_height - 80) / 2) - len(net_out)/2*font_size)
            for i, val in enumerate(net_out):
                val_txt = font.render(str(np.around(val, 2)), False, (255,255,255))
                val_txt_dest_x = ((self.sidebar_width-60)/4+20) - val_txt.get_rect().width / 2 + (self.sidebar_width-60)/2 + 20
                pygame.draw.rect(gameDisplay, (0,0,0), (40 + (self.sidebar_width-60)/2, out_beginning_y + 60 + i*(font_size+1), (self.sidebar_width-60)/2, font_size+2))
                gameDisplay.blit(val_txt, (val_txt_dest_x, 60 + out_beginning_y + i*font_size))

    def _display_info(self, creature_locs) -> None:
        pos = pygame.mouse.get_pos()
        if pos[0] >= self.sidebar_width and pos[1] > self.y:
            relatives_per_pixel = self.relatives_on_screen / self.display_height
            relative_mouse_x = (pos[0] - self.sidebar_width) * relatives_per_pixel
            relative_mouse_y = (pos[1]-self.y) * relatives_per_pixel
            tile_x = int(self.relative_x//10 + relative_mouse_x // 10)
            tile_y = int(self.relative_y//10 + relative_mouse_y // 10)
            info = [np.round(self.grid[tile_x, tile_y], 2), tile_x, tile_y]

            pixels_per_relative = self.display_height / self.relatives_on_screen 

            font = get_font(int(3 * pixels_per_relative)) # add to zoom

            info_surf = pygame.Surface((pixels_per_relative*10, pixels_per_relative*10), pygame.SRCALPHA, 32)
            h_txt = font.render("h: "+str(info[0][0]), False, (0,0,0))
            s_txt = font.render("s: "+str(info[0][1]), False, (0,0,0))
            v_txt = font.render("h: "+str(info[0][2]), False, (0,0,0))
            info_surf.blit(h_txt, (pixels_per_relative, pixels_per_relative))
            info_surf.blit(s_txt, (pixels_per_relative, pixels_per_relative*4))
            info_surf.blit(v_txt, (pixels_per_relative, pixels_per_relative*7))
            self.map_surf.blit(info_surf, (tile_x*10*pixels_per_relative - self.relative_x*pixels_per_relative, tile_y*10*pixels_per_relative - self.relative_y*pixels_per_relative))