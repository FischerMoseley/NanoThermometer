from phidl import Path, CrossSection, Device, LayerSet
from phidl import quickplot as qp
import phidl.geometry as pg
import phidl.path as pp
import numpy as np

def merge(geometry_list, layer):
    combined_geometry = geometry_list[0]
    
    for geometry in geometry_list[1:]:
        combined_geometry = pg.boolean(A = combined_geometry, B = geometry, operation = 'A+B', precision = 1e-6, layer = layer)

    return combined_geometry

# outline so you know where to draw things
def draw_outline(layer):
    # Draw the circle and text surrounding the device. Taken from the lab 2 MEMS code.
    
    top_text = pg.text(text="6.152J Lab 3 - Spring 2022", size=4000, justify='center', layer=2, font="Arial").move( (0, 36000) )
    bottom_text = pg.text(text="Fischer Moseley",  size=3000, justify='center', layer=2, font="Arial" ).move( (0, -30000) )
    ring = pg.ring(radius = 51000, width = 500, angle_resolution = 2.5, layer = 2)
    
    text = pg.boolean(A = top_text, B = bottom_text, operation = 'A+B', precision = 1e-6, layer=2)
    return pg.boolean(A = text, B = ring, operation = 'A+B', precision = 1e-6, layer=layer)
    

def label(text, layer, fontsize = 100):
    # Takes the width and length of the cantilever as parameters,
    # and generates an appropriate label.
    # This gets etched into the top metal.
    return pg.text(text=text, size=fontsize, justify='left', layer=layer, font="DEPLOF" )

def contact_pad(layer):
    return pg.rectangle(size = (250, 250), layer=layer)

def heater(width, radius, length, pitch, squiggles, layer):
    # Make Heater
    
    
    # Make heater coil
    points = [(0,0)]
    for i in range(0, squiggles,2):
        points.append( (length, i*pitch) )
        points.append( (length, (i+1)*pitch) )
        points.append( (0, ((i+1)*pitch)) )
        points.append( (0, ((i+2)*pitch)) )
    
    # this is a hack, but remove the last point
    points = points[:-1]
    last_point = points[-1]
    points = np.array(points)
    
    P = pp.smooth(
        points = points,
        radius = radius,
        corner_fun = pp.arc)
    
    X = CrossSection()
    X.add(width = width, offset = 0, layer = layer)
    coil = P.extrude(X)
    
    
    # Connect contact pads to heater coil
    end_x = last_point[0]
    end_y = last_point[1]
    
    top_bar = pg.rectangle(size = (250, width), layer=layer).move((-250,end_y-width/2))
    bottom_bar = pg.rectangle(size = (250, width), layer=layer).move((-250,-width/2))
    
    # Make contact pads
    top_pad = contact_pad(layer=layer).move((-400,end_y-width/2))
    bottom_pad = contact_pad(layer=layer).move((-400,-width/2))
    
    
    return merge([coil, top_pad, bottom_pad, top_bar, bottom_bar], layer=layer)


def litho_ruler(
    height=2,
    width=15,
    spacing=30,
    scale=[30, 10, 10, 10, 10, 20, 10, 10, 10, 10],
    num_marks=25,
    layer=1):

    D = Device("litho_ruler")
    for n in range(num_marks):
        h = height * scale[n % len(scale)]
        D << pg.rectangle(size=(width, h), layer=layer)

    D.distribute(direction="x", spacing=spacing, separation=False, edge="x")
    D.align(alignment="ymin")
    D.flatten()
    return pg.extract(D, layers = [1])

def cross(length, width, layer):
    D = Device(name="cross")
    R = pg.rectangle(size=(width, length), layer=layer)
    r1 = D.add_ref(R).rotate(90)
    r2 = D.add_ref(R)
    r1.center = (0, 0)
    r2.center = (0, 0)
    return pg.extract(D, layers = [1])


def cantilever(pit_width, gap_size, beam_width, beam_length, layer, tip):
    # Make cantilever, and the etch pit below it.
    # Length corresponds to x distance, width is y distance. 
    # This seems backwards, but that's because it's from the perspective of the beam.
   

    if tip:
        # tip makes an equilateral triangle at the tip instead of leaving it blunt
        tip_length = beam_width * np.cos(np.pi/6)
        pit_length = beam_length + tip_length + gap_size
        

        beam_tip = pg.taper(length = tip_length, width1 = beam_width, width2 = 0, layer = 2).move((beam_length - tip_length, 0))
        edge_tip = pg.taper(length = tip_length, width1 = beam_width, width2 = 0, layer = 2).rotate(angle=180).move((pit_length, 0))
        bar = pg.rectangle(size = (beam_length - tip_length, beam_width), layer = 2).move((0,-beam_width/2))
        
        geometry = pg.boolean(A = beam_tip, B = edge_tip, operation = 'A+B', precision = 1e-6)
        geometry = pg.boolean(A = geometry, B = bar, operation = 'A+B', precision = 1e-6)
        
        etch_pit = pg.rectangle( size = (pit_length, pit_width), layer=2 ).move( (0,-pit_width/2) )
        return pg.boolean(A = etch_pit, B = geometry, operation = 'A-B', precision = 1e-6, layer = layer)
        
        
    else:
        pit_length = beam_length + gap_size
        etch_pit = pg.rectangle( size = (pit_length, pit_width), layer=2 ).move( (0,-pit_width/2) )
        beam = pg.rectangle( size = (beam_length, beam_width), layer=2 ).move( (0,-beam_width/2) ) 
        return pg.boolean(A = etch_pit, B = beam, operation = 'A-B', precision = 1e-6, layer = layer)
    

def device_nitride(pit_width, gap_size, beam_width, beam_length, tip):
    # Assemble all the parts needed to make the device!     
    return cantilever(pit_width=pit_width, gap_size=gap_size, beam_width=beam_width, beam_length=beam_length, layer = 2, tip=tip)

def device_gold(pit_width, gap_size, beam_width, beam_length, tip):
    
    # Make body of device
    c_mask = cantilever(pit_width, gap_size, beam_width, beam_length, layer=2, tip=tip)
    au_mask = pg.rectangle(size = (700, pit_width), layer = 2).move((-50,-300))
    d = pg.boolean(A=au_mask, B=c_mask, operation='A-B', layer = 1)
       
    # Add contact pads
    left_pad = contact_pad(layer = 1).move((-250,300+125))
    right_pad = contact_pad(layer = 1).move((450,300+125))
    
    # Connect contact pads to cantilever arms
    left_busbar = pg.rectangle(size = (50, 600), layer = 2).move((-50,-100))
    right_busbar = pg.rectangle(size = (50, 800), layer = 2).move((650,-300))
    
    
    # Make label text above
    buffer = 180 # how much space between label text and top edge of the etch pit
    l = label(text = f'{beam_width}/{beam_length}/{gap_size}', layer=1).move((-850, -pit_width/2 - buffer))
    
    # Make heater on the side
    h = heater(width = 15, radius = 20, length=300, pitch=60, squiggles = 10, layer = 1).move((-420,-280))
    
    # Make scale for the side
    bottom_ruler = litho_ruler(layer = 1).move((-50,-450))
    side_ruler = litho_ruler(layer = 1).rotate(-90).move((750, 300))
    
    return merge([d, h, l, bottom_ruler, side_ruler, left_pad, right_pad, left_busbar, right_busbar], layer = 1)


# Hierarchy:
# - Wafer
#   - Outline
#   - Grid
#     - Cluster
#       - Device
#         - Label
#         - Heater Coil
#         - Heater Pads
#         - Trench
#         - Cantilever 
#         - Contact and tips 

# Layer Stack:
# - Layer 0: Gold
# - Layer 1: Silicon Nitride
# - Layer 2: Internal stuff, not for fab


def wafer():
    # Layout the wafer of devices
    W = Device('wafer')
    
    x_spacing = 1800
    y_spacing = 1220
    
    ## Wide beam width devices (100um)
    # Grace us our lord on high for the tip
    for i, gap_size in enumerate([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]):
        for j, beam_length in enumerate([50, 75, 100, 150, 200, 300, 400, 500]):
            W << device_gold(pit_width=600, gap_size=gap_size, beam_width=100, beam_length=beam_length, tip=True).move((x_spacing*i,y_spacing*j)).move((0,0))
            W << device_nitride(pit_width=600, gap_size=gap_size, beam_width=100, beam_length=beam_length, tip=True).move((x_spacing*i,y_spacing*j)).move((0,0))
    
    # Blunt tip
    for i, gap_size in enumerate([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]):
        for j, beam_length in enumerate([50, 75, 100, 150, 200, 300, 400, 500]):
            W << device_gold(pit_width=600, gap_size=gap_size, beam_width=100, beam_length=beam_length, tip=False).move((x_spacing*i,y_spacing*j)).move((0,-10600))
            W << device_nitride(pit_width=600, gap_size=gap_size, beam_width=100, beam_length=beam_length, tip=False).move((x_spacing*i,y_spacing*j)).move((0,-10600))
            
    # Grace us our lord on high for the tip (again)
    for i, gap_size in enumerate([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]):
        for j, beam_length in enumerate([50, 75, 100, 150, 200, 300, 400, 500]):
            W << device_gold(pit_width=600, gap_size=gap_size, beam_width=100, beam_length=beam_length, tip=True).move((x_spacing*i,y_spacing*j)).move((0,-21200))
            W << device_nitride(pit_width=600, gap_size=gap_size, beam_width=100, beam_length=beam_length, tip=True).move((x_spacing*i,y_spacing*j)).move((0,-21200))
    
    # Blunt tip (again)
    for i, gap_size in enumerate([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]):
        for j, beam_length in enumerate([50, 75, 100, 150, 200, 300, 400, 500]):
            W << device_gold(pit_width=600, gap_size=gap_size, beam_width=100, beam_length=beam_length, tip=False).move((x_spacing*i,y_spacing*j)).move((0,-31800))
            W << device_nitride(pit_width=600, gap_size=gap_size, beam_width=100, beam_length=beam_length, tip=False).move((x_spacing*i,y_spacing*j)).move((0,-31800))
             
             
             
    ## Thin beam width devices (50um)
    # Grace us our lord on high for the tip
    for i, gap_size in enumerate([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]):
        for j, beam_length in enumerate([50, 75, 100, 150, 200, 300, 400, 500]):
            W << device_gold(pit_width=600, gap_size=gap_size, beam_width=50, beam_length=beam_length, tip=True).move((x_spacing*i,y_spacing*j)).move((16500,0))
            W << device_nitride(pit_width=600, gap_size=gap_size, beam_width=50, beam_length=beam_length, tip=True).move((x_spacing*i,y_spacing*j)).move((16500,0))
     
    # Blunt tip
    for i, gap_size in enumerate([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]):
        for j, beam_length in enumerate([50, 75, 100, 150, 200, 300, 400, 500]):
            W << device_gold(pit_width=600, gap_size=gap_size, beam_width=50, beam_length=beam_length, tip=False).move((x_spacing*i,y_spacing*j)).move((16500,-10600))
            W << device_nitride(pit_width=600, gap_size=gap_size, beam_width=50, beam_length=beam_length, tip=False).move((x_spacing*i,y_spacing*j)).move((16500,-10600))
             
    # Grace us our lord on high for the tip (again)
    for i, gap_size in enumerate([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]):
        for j, beam_length in enumerate([50, 75, 100, 150, 200, 300, 400, 500]):
            W << device_gold(pit_width=600, gap_size=gap_size, beam_width=50, beam_length=beam_length, tip=True).move((x_spacing*i,y_spacing*j)).move((16500,-21200))
            W << device_nitride(pit_width=600, gap_size=gap_size, beam_width=50, beam_length=beam_length, tip=True).move((x_spacing*i,y_spacing*j)).move((16500,-21200))
     
    # Blunt tip (again)
    for i, gap_size in enumerate([1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]):
        for j, beam_length in enumerate([50, 75, 100, 150, 200, 300, 400, 500]):
            W << device_gold(pit_width=600, gap_size=gap_size, beam_width=50, beam_length=beam_length, tip=False).move((x_spacing*i,y_spacing*j)).move((16500,-31800))
            W << device_nitride(pit_width=600, gap_size=gap_size, beam_width=50, beam_length=beam_length, tip=False).move((x_spacing*i,y_spacing*j)).move((16500,-31800))
            
    return W

W = wafer()
#W << draw_outline(layer=2)
W << cross(length = 100, width = 20, layer = 1).move((-1200, 9600))
W << cross(length = 100, width = 20, layer = 1).move((33000,9600))
W << cross(length = 100, width = 20, layer = 1).move((-1200, -32000))
W << cross(length = 100, width = 20, layer = 1).move((33000,-32000))


# write to file
W.write_gds('C:\\Users\\fischerm\\Documents\\GitHub\\NanoThermometer\\fischerm.gds')