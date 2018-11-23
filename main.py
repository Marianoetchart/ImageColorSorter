import os
import shutil
import cv2
import math
import pygame
from PIL import Image
import warnings
import json

class ImageSorter:
        # Class to copy and sort images to directories according to color.
    def __init__(self, image_types=["jpg", "PNG", "JPEG"], dir_path="C:\\Images", starting_dir="\\"):
        self.image_types = tuple(image_types)
        self.dir_path = dir_path
        self.counter = 0
        self.copy_list = []
        self.starting_dir = starting_dir
        self.print_warnings = False

    def copy_images_2_dir(self):
        self.recursive_dir_walk(self.starting_dir)
        self.copy_files(self.copy_list, self.dir_path)
        print('Copying finished. Copied {0} files to directory'.format(self.counter))

        # Walks through OS starting in starting_dir  and copies file names ending in parameter image_types to a list
        # to later do the copy operation
    def recursive_dir_walk(self, starting_dir):

        # for root, dirs, files in os.walk(starting_dir):
        #     if files is []:
        #         continue
        #     if root is not self.dir_path:
        #         for file_name in files:
        #             if os.path.join(root, file_name).endswith(self.image_types):
        #                 print(os.path.join(root, file_name))
        #                 self.copy_list.append(os.path.join(root, file_name))

        print("Resursively walking directories...")
        for root, dirs, files in os.walk(starting_dir):
            if dirs is []:
                if files is []:
                    return
                if root is not self.dir_path:
                    for file_name in files:
                        if os.path.join(root, file_name).endswith(self.image_types):
                            self.copy_list.append(os.path.join(root, file_name))
                return
            if files is not [] and root is not self.dir_path:
                for file_name in files:
                    if os.path.join(root, file_name).endswith(self.image_types):
                        self.copy_list.append(os.path.join(root, file_name))
            for name in dirs:
                self.recursive_dir_walk(os.path.join(root, name))
            return

        # copies a list of paths into the destination directory (dir_path)
    def copy_files(self, list_of_paths, dir_path):
        for path in list_of_paths:
            try:
                if os.path.exists(dir_path):
                    #print('copying {0}'.format(path))
                    shutil.copy(path, dir_path)
                    self.counter += 1
                elif not (os.path.exists(dir_path)):
                    os.makedirs(dir_path)
                    #print('copying {0}'.format(path))
                    shutil.copy(path, dir_path)
                    self.counter += 1
            except Exception as e:
                if self.print_warnings == True:
                    warnings.warn(str(e))
            print("Copying {0} images.".format(self.counter), end = '\r')      

        # sorts the images in color directories by using average color of image and default RGB values of colors.
    def sort_by_color(self):
        colors = ["red", "green", "blue", "yellow", "brown"]
        # color RGB map
        rgb_list = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0], [165, 42, 42]]

        # checking if color folders exists, if not, create
        for color in colors:
            if not(os.path.exists(os.path.join(self.dir_path, color))):
                os.makedirs(os.path.join(self.dir_path, color))

        # sorting and copying
        for file in os.listdir(self.dir_path):
            img_path = os.path.join(self.dir_path, file)
            img = cv2.imread(img_path)
            L2_distances = []
            if img is not None:
                average_color = [img[:, :, i].mean() for i in range(img.shape[-1])]
                average_color.reverse()
                for rgb_values in rgb_list:
                    difference_squared = [((a_c - b)**2) for a_c, b in zip(average_color, rgb_values)]
                    summation = sum(difference_squared)
                    L2_distances.append(math.sqrt(summation))
                try:
                    index_min, value_min = min(enumerate(L2_distances), key=lambda p: p[1])
                    self.copy_files([img_path], os.path.join(self.dir_path, colors[index_min]))
                except Exception as e:
                    if self.print_warnings == True:
                        warnings.warn(str(e))
            else:
                if self.print_warnings == True:
                    warnings.warn("Could not sort image {0} as it is None".format(file))

# UI to crop images with a rectangle and store meta data.
class ImageCropper:
    def __init__(self, img_path, output_path="C:\\Images\\Cropped"):
        pygame.init()
        self.img_path = img_path
        self.output_path = output_path

        #loading image with pygame
        self.px = pygame.image.load(self.img_path)
        self.screen = pygame.display.set_mode(self.px.get_rect()[2:])
        self.screen.blit(self.px, self.px.get_rect())
        pygame.display.flip()

        #main UI loop only returning when rectangle clicks are complete
        left, upper, right, lower = self.main_loop()

        # Making sure rectangle is right way around.
        if right < left:
            left, right = right, left
        if lower < upper:
            lower, upper = upper, lower

        # saving image
        im = Image.open(self.img_path)
        im = im.crop((left, upper, right, lower))
        pygame.display.quit()
        if not (os.path.exists(self.output_path)):
            os.makedirs(self.output_path)
        im.save(os.path.join(self.output_path, os.path.basename(self.img_path)))
        print("Saved cropped image to {0}".format(self.output_path))

        # storing meta data
        self.save_meta_data(im, (left, upper, right, lower))

    def main_loop(self):
        topleft = bottomright = prior = None
        done = False
        while done is not True:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONUP:
                    if not topleft:
                        topleft = event.pos
                    else:
                        bottomright = event.pos
                        done = True
            if topleft:
                prior = self.display_image(topleft, prior)
        return (topleft + bottomright)

    def display_image(self, topleft, prior):
        # ensure that the rect always has positive width, height
        x, y = topleft
        width = pygame.mouse.get_pos()[0] - topleft[0]
        height = pygame.mouse.get_pos()[1] - topleft[1]
        if width < 0:
            x += width
            width = abs(width)
        if height < 0:
            y += height
            height = abs(height)

        # eliminate redundant drawing cycles (when mouse isn't moving)
        current = x, y, width, height
        if not (width and height):
            return current
        if current == prior:
            return current

        # draw transparent box and blit it onto canvas
        self.screen.blit(self.px, self.px.get_rect())
        im = pygame.Surface((width, height))
        im.fill((128, 128, 128))
        pygame.draw.rect(im, (32, 32, 32), im.get_rect(), 1)
        im.set_alpha(128)
        self.screen.blit(im, (x, y))
        pygame.display.flip()

        # return current box
        return (x, y, width, height)

    def save_meta_data(self, image, coordinates):

        file_name = os.path.basename(self.img_path)
        file_path = os.path.join(self.output_path, os.path.basename(self.img_path))
        left, upper, right, lower = coordinates
        img_resolution = image.size

        data = {}
        data['Filename'] = file_name
        data['File Path'] = file_path
        data['Coordinates'] = [left, upper, right, lower]
        data['Image Resolution'] = img_resolution

        json_file_name= os.path.splitext(file_path)[0] + ".txt"
        print(json_file_name)
        with open(json_file_name, 'w') as outfile:
            json.dump(data, outfile)

        print("Saved meta data to {0}".format(self.output_path))


if __name__ == "__main__":
    print('Starting copier')
    ics = ImageSorter()
    ics.copy_images_2_dir()
    ics.sort_by_color()
    print('Starting cropper')
    ic = ImageCropper("C:\\Users\\Mariano\\Pictures\\5595fceaa3610.jpg")









