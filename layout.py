from phidl import Path, CrossSection, Device, LayerSet
from phidl import quickplot as qp
import phidl.geometry as pg
import phidl.path as pp
import numpy as np

# outline so you know where to draw things

# making the little squiggles <3
def draw_sign():
    S = Device('sign')

    # make low frequency sine wave
    length = 2500
    amplitude = 900
    periods = 1
    def my_custom_offset_fun(t):
        return amplitude + amplitude*np.cos(2*np.pi*t * periods)


    P = pp.straight(length = length)
    X = CrossSection()
    X.add(width = 200, offset = my_custom_offset_fun, layer = 2)
    S << P.extrude(X).move((2500, 6000))


    # make text
    S << pg.text(text="2/18/22", size=250, justify='left', layer=2, font='DEPLOF').move((6000, 7000))

    return S


def draw_outline(W):
    # Draw the circle and text surrounding the device. Taken from the lab 2 MEMS code.
    W << pg.ring(radius = 51000, width = 500, angle_resolution = 2.5, layer = 2)
    W << pg.text(text="6.152J Lab 3 - Spring 2022", size=4000, justify='center', layer=2, font="Arial").move( (0, 36000) )
    W << makeCutout(pg.text(text="Fischer Moseley",  size=3000, justify='center', layer=2, font="Arial" ).move( (0, -30000) ),line=10,space=10,layer=2)

def label(width, length, fontsize = 150, layer = 2):
    # Takes the width and length of the cantilever as parameters,
    # and generates an appropriate label.
    # This gets etched into the top metal.
    label_text = f'{width}/{length}'
    return pg.text(text=label_text, size=fontsize, justify='left', layer=layer, font="Arial" )#.move( (0,params.cutheight/2+params.buffer + params.trench + params.fontsize/2) )


def cantilever(C, pit_width, pit_length, beam_width, beam_length, layer=1, tip=True):
    # Make cantilever, and the etch pit below it.
    # Length corresponds to x distance, width is y distance. 
    # This seems backwards, but that's because it's from the perspective of the beam

    etch_pit = pg.rectangle( size = (pit_length, pit_width), layer=2 ).move( (0,-pit_width/2) )

    if tip:
        # tip makes an equilateral triangle at the tip instead of leaving it blunt
        
        tip_length = beam_width * np.cos(np.pi/6)
        tip = pg.taper(length = tip_length, width1 = beam_width, width2 = 0, layer = 2).move((beam_length - tip_length, 0))
        bar = pg.rectangle(size = (beam_length - tip_length, beam_width), layer = 2).move((0,-beam_width/2))   
        beam = pg.boolean(A = bar, B = tip, operation = 'A+B', precision = 1e-6)
        
    else:
        beam = pg.rectangle( size = (beam_width, beam_length), layer=2 ).move( (0,-beam_length/2) )   
    

    C << pg.boolean(A = etch_pit, B = beam, operation = 'A-B', precision = 1e-6, layer = layer)


# Hierarchy:
# - Wafer
#   - Outline
#   - Grid
#     - Chunk
#       - Device
#         - Label
#         - Heater
#         - Trench DONE
#         - Cantilever DONE


W = Device('Wafer')
#draw_outline(W)
cantilever(W,600, 600, 100, 300)


qp(W)

# write to file
W.write_gds('C:\\Users\\fischerm\\Documents\\GitHub\\NanoThermometer\\fischerm.gds')