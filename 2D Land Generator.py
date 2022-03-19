from PIL import Image
import random
import math
from opensimplex import OpenSimplex

def ExportArray(input_array, filename, colorKey):
    """Processes 2D array to RGB data."""
    colors = []
    width = len(input_array[0])
    height = len(input_array)
    # Goes through 2D array and process it into RGB values.
    for Y in range(height):
        for X in range(width):
            colors.extend(colorKey[input_array[Y][X]])

    # Converting RGB list into something pillow can use to save an image.
    colors = bytes(colors)
    img = Image.frombytes('RGB', (width, height), colors)
    img.save(f'{filename}.png')
    # Letting user know the image is saved.
    print(f'{filename}.png Saved')

def Scale(Noise, Width, Height):
    '''Scales an array up.'''
    temp_Noise = []
    Ori_Width = len(Noise[0]) / Width
    Ori_Height = len(Noise) / Height

    for Y in range(Height):
        temp_Noise.append([])
        for X in range(Width):
            temp_Noise[Y].append(Noise[int(Y * Ori_Height)][int(X * Ori_Width)])
    return temp_Noise

def ScaleBetween(unscaledNum, minAllowed, maxAllowed, min, max):
    # https://stackoverflow.com/questions/5294955/how-to-scale-down-a-range-of-numbers-with-a-known-min-and-max-value
    return (maxAllowed - minAllowed) * (unscaledNum - min) / (max - min) + minAllowed

def GetCoord(x, y):
    global WIDTH, HEIGHT, Noise
    if x < 0 or x >= WIDTH:
        return 96
    elif y < 0 or y >= HEIGHT:
        return 96
    else:
        return Noise[int(y)][int(x)]

def CellularAutomata(old_noise, width, height):
    """Uses Cellular Automata for the purpose of smoothing the array"""
    Processed_Noise = []
    for Y in range(height):
        Processed_Noise.append([])
        for X in range(width):
            color = old_noise[Y][X]
            if color == 224:
                Processed_Noise[Y].append(224)
            else:
                Wall_Count = 0
                check = 96
                if GetCoord(X, Y - 1) == check:
                    Wall_Count += 1
                if GetCoord(X - 1, Y - 1) == check:
                    Wall_Count += 1
                if GetCoord(X + 1, Y - 1) == check:
                    Wall_Count += 1
                if GetCoord(X, Y) == check:
                    Wall_Count += 1
                if GetCoord(X - 1, Y) == check:
                    Wall_Count += 1
                if GetCoord(X + 1, Y) == check:
                    Wall_Count += 1
                if GetCoord(X, Y + 1) == check:
                    Wall_Count += 1
                if GetCoord(X - 1, Y + 1) == check:
                    Wall_Count += 1
                if GetCoord(X + 1, Y + 1) == check:
                    Wall_Count += 1
                if Wall_Count > 4:
                    Processed_Noise[Y].append(96)
                else:
                    Processed_Noise[Y].append(32)
    old_noise = Processed_Noise
    return old_noise

def Turbulence(x, y, size):
    """Applies turbulence and returns the value"""
    # Gotten from the Marble Section https://lodev.org/cgtutor/randomnoise.html
    value = 0.0
    initialSize = size

    while(size >= 1):
        value += tempFG.noise2d(x / size, y / size) * size
        size /= 2.0

    return (128.0 * value / initialSize)

# Image Colors.
colorKey = {
    224 : [128,196,255], # Sky
    96 : [96,96,96], # Foreground
    32 : [32,32,32], # Background
    900 : [255, 0, 0] # Should Never Appear
}


# Image Data
WIDTH = 512
HEIGHT = 256
Noise = []
# Rendering Settings
FGWall = 0 # Stone Threshold This is best between -0.5 and 0.3
skyCutOff = 128 # Lowest point in which cave/solid transition begins. If this is above skyUpperCutOff caves will generate above it
skyUpperCutOff = 64 # Highest Point in which caves can generate


# Generator Settings         Pre-made Settings #1     #2      #3
xPeriod = 16     # How Squished the X Axis is  32     128.0   16
yPeriod = 8      # How Squished the Y Axis is  256    192.0   8
turbPower = 2.5  # The Turbulence Power        1.5    4.0     2.5
turbSize = 16    # Intensity of Turbulence     32.0   32.0    16
# Initialize Simplex Noise and Random Num Generator
random.seed() # Leave Blank for random
tempFG = OpenSimplex(random.randint(0,100000))
# Iterations of Cellular Automata Applied
Iterations = 3


#Empty World
for Y in range(HEIGHT):
    Noise.append([])
    for X in range(WIDTH):
        Noise[Y].append(224)

# Terrain
for X in range(WIDTH):
    Y = int(ScaleBetween(tempFG.noise2d(X/64, 3)+tempFG.noise2d(X/32, 2)/2+tempFG.noise2d(X/16, 3)/4+tempFG.noise2d(X/8, 3)/8, 0, skyUpperCutOff, -1.875, 1.875)+skyUpperCutOff/3)
    for Y_Max in range(HEIGHT-Y):
        Noise[Y + Y_Max][X] = 96

# Foreground
for Y in range(HEIGHT):
    for X in range(WIDTH):
        xyValue = tempFG.noise2d(X / (xPeriod*2), Y / (yPeriod*2)) + tempFG.noise2d(X / xPeriod, Y / yPeriod) + turbPower * -Turbulence(X, Y, turbSize) / 256.0
        temp = (math.sin(xyValue * 3.14159))

        if Y < skyCutOff: # Sets caves. If it fulfills the condition the area lies in the cutoff zone.
            if Y > skyUpperCutOff and temp + -(ScaleBetween(Y, -1, 0, skyUpperCutOff, skyCutOff)) < FGWall:  # Sky Transition Area
                if Noise[Y][X] != 224: # Ensures caves do not generate in the air
                    Noise[Y][X] = 900
        elif Noise[Y][X] != 224: # Ensures caves do not generate in the air
            if temp < FGWall:
                Noise[Y][X] = 32
            else:
                Noise[Y][X] = 96

# Smooth the Terrain
for i in range(Iterations):
    Noise = CellularAutomata(Noise, WIDTH, HEIGHT)

# Scale Up Final Image
Noise = Scale(Noise, WIDTH*2, HEIGHT*2)

ExportArray(Noise, "2D Land Generation", colorKey)