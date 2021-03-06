
<!-- saved from url=(0063)http://registry.gimp.org/files/seamless_advanced_v1.16.py_0.txt -->
<html><head><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1"><style type="text/css"></style><style type="text/css"></style></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;"># Make Seamless Advanced v1.16
# (copyLEFT) 2013 Andrey "Efenstor" Pivovarov. No rights reserved
# Copy freely, modify freely, spread the word and remeber me in your prayers

# Using the "Manual overlap" function:

# 1. Set "Horizontal overlap" to the value you need and "Vertical overlap" to 0
# 2. (optionally) Turn on "Hi-pass pre-filter"
# 3. Click OK
# 4. Edit the overlap to make it seamless. Don't worry about the top and bottom
#    edge correspondence - this corner will be covered by the vertical overlap.
# 5. Merge down
# 6. Start the plugin again
# 7. Now set "Vertical overlap" to the value you need and "Horizontal overlap"
#    to 0
# 8. (optionally) Turn off "Hi-pass pre-filter"
# 9. Click OK
# 10. Edit the overlap to make it seamless. This time you MUST care about left
#     and right edge correspondence; in the most cases it has no need be very
#     precise.
# 11. Merge down

# New in the version 1.16:
# * Fixed crash if the hi-pass was on and any of the overlap values was 0
#   (which is vital for the manual overlap mode)

# New in the version 1.15:
# * Greatly improved hi-pass filter (now on by default)
# * Now overlap values are checked against the image dimensions, if larger the
#   maximum recommended value is displayed

# New in the version 1.11:
# * Manual overlap mode with both horizontal and vertical overlaps specified
#   simultaneously is now explicitly disallowed (a warning message will be
#   given)

# New in the version 1.1:
# * Hi-pass pre-filter added (thanks to RPG for the idea)
# * Another fuzziness anti-aliasing method (now only a toggle)


#!/usr/bin/env python

import math
from gimpfu import *

def msa_deinit(img):

    # Deinitialize the plugin
    pdb.gimp_undo_push_group_end(img)
    pdb.gimp_progress_end()
    pdb.gimp_displays_flush()


def msa_proc(img, ovr, ovr_mask, off, gcontr, gfuzzy, gradtype):

    # Shift and crop
    ovr.translate(img.width-off, 0)
    pdb.gimp_image_crop(img, img.width-off, img.height, off, 0)
    
    # Gradient
    if gradtype==0:
       # Simple gradient
       pdb.gimp_context_set_default_colors()
       pdb.gimp_edit_blend(ovr_mask, 0, 0, 0, 100, .5, 0, FALSE, FALSE, 5, 0, TRUE, 0, 0, off, 0)
    else:
       # Intelligent gradient
       pdb.gimp_context_set_default_colors()
       pdb.gimp_edit_blend(ovr_mask, 2, 0, 0, 100, .5, 0, FALSE, FALSE, 5, 0, TRUE, 0, 0, off/2, 0)
       pdb.gimp_context_swap_colors()
       pdb.gimp_edit_blend(ovr_mask, 2, 0, 0, 100, .5, 0, FALSE, FALSE, 5, 0, TRUE, off, 0, (off/2)+1, 0)
       
    # Gradient contrast
    if gcontr&gt;0:
       gc = int((gcontr/100)*127+.5)
       pdb.gimp_brightness_contrast(ovr_mask, 0, gc)
       
    # Gradient fuzziness
    if gfuzzy&gt;0:
       pdb.gimp_layer_resize_to_image_size(ovr)
       pdb.plug_in_spread(img, ovr_mask, gfuzzy, gfuzzy)
       pdb.plug_in_blur(img, ovr_mask)


def make_seamless_advanced(img, layer, ho, vo, gcontr, gfuzzy, gradtype, hipass, hpblur, manual, flatten):

    # Check the initial requirements
    if ho&gt;img.width/2 or vo&gt;img.height/2:
       # Overlap should be smaller than half the image dimension
       if ho&gt;img.width/2:
          pdb.gimp_message("Horizontal overlap should be no larger than "+str(img.width/2)+" px for this image. Please decrease it.")
       if vo&gt;img.height/2:
          pdb.gimp_message("Vertical overlap should be no larger than "+str(img.height/2)+" px for this image. Please decrease it.")
       return
    if manual and ho&gt;0 and vo&gt;0:
       # Both horizontal and vertical are not allowed in the manual mode
       pdb.gimp_message("When using the manual overlap mode please set one of the overlap values (either vertical or horizontal) to zero.\n\nFor detailed instructions on how to use the manual mode visit http://registry.gimp.org/node/28112 or open the plugin file (seamless_advanced_v1.16.py) in a text editor.")
       return
       
    # Initialization
    gimp.progress_init("Preparing...")
    pdb.gimp_undo_push_group_start(img)

    # Hi-pass pre-filter
    if hipass&gt;0:
       # Add the subtraction layer
       hps = layer.copy()
       hps.name = "Subtraction"
       img.active_layer = layer   # Mind its correct position
       img.add_layer(hps, -1)
       hps.mode = 20   # GRAIN-EXTRACT-MODE
              
       # Process it
       pdb.gimp_desaturate_full(hps, 1)
       if hpblur==0:
          if ho==0 or vo==0:
             if ho&gt;0: gaua = ho
             elif vo&gt;0: gaua = vo
             elif img.width&lt;img.height: gaua = img.width*.25
             else: gaua = img.height*.25
          elif ho&lt;vo: gaua = ho
          else: gaua = vo
       elif img.width&lt;img.height: gaua = img.width*(hpblur/100)
       else: gaua = img.height*(hpblur/100)
       pdb.plug_in_gauss(img, hps, gaua, gaua, 1)
       
       # Add a layer to merge down on
       bkcp = layer.copy()
       bkcp.name = "Background copy"
       img.active_layer = layer   # Mind its correct position
       img.add_layer(bkcp, -1)
       
       # Merge down
       hp1 = pdb.gimp_image_merge_down(img, hps, 1)
       hp1.name = "Hi-pass stage 1"
       
       # Add the equalization layer
       hpe = layer.copy()
       hpe.name = "Equalization"
       img.active_layer = hp1   # Mind its correct position
       img.add_layer(hpe, -1)
       hpe.mode = 5   # OVERLAY-MODE
       
       # Process it
       pdb.plug_in_pixelize2(img, hpe, img.width, img.height)
       pdb.gimp_desaturate_full(hpe, 0)

       # Merge down and strip off alpha
       layer = pdb.gimp_image_merge_down(img, hpe, 1)
       layer.name = "Hi-pass"
       pdb.gimp_layer_flatten(layer)

    # Manual
    if manual:
       if ho&gt;0:
          hor = layer.copy()
          hor.name = "Horizontal overlap"
          img.add_layer(hor, -1)
          hor_mask = hor.create_mask(0)
          hor.add_mask(hor_mask)
          hor.translate(img.width-ho, 0)
          pdb.gimp_image_crop(img, img.width-ho, img.height, ho, 0)
       if vo&gt;0:
          ver = layer.copy()
          ver.name = "Vertical overlap"
          img.add_layer(ver, -1)
          ver_mask = ver.create_mask(0)
          ver.add_mask(ver_mask)
          ver.translate(0, img.height-vo)
          pdb.gimp_image_crop(img, img.width, img.height-vo, 0, vo)
       msa_deinit(img)
       return
       
    if ho&gt;0:
       # Make the horizonal overlap layer
       hor = layer.copy()
       hor.name = "Horizontal overlap"
       img.active_layer = layer   # Mind its correct position
       img.add_layer(hor, -1)
       if gradtype==1: hor_mask = hor.create_mask(5)
       else: hor_mask = hor.create_mask(0)
       hor.add_mask(hor_mask)

       # Do horizontal tiling (actually it always will be horizontal :)
       msa_proc(img, hor, hor_mask, ho, gcontr, gfuzzy, gradtype)   
       
       if vo&gt;0:
          # Copy the background
          bkcp = layer.copy()
          bkcp.name = "Background copy"
          img.active_layer = hor   # Mind its correct position
          img.add_layer(bkcp, -1)    
          
          # Copy the horizontal overlap layer
          horcp = hor.copy()
          horcp.name = "Horizontal overlap copy"
          img.active_layer = bkcp   # Mind its correct position
          img.add_layer(horcp, -1)
          
          # Merge down, strip alpha and add the mask
          ver = pdb.gimp_image_merge_down(img, horcp, 0)
          ver.name = "Vertical overlap"
          pdb.gimp_layer_flatten(ver)
          if gradtype==1: ver_mask = ver.create_mask(5)
          else: ver_mask = ver.create_mask(0)
          ver.add_mask(ver_mask)
          # Now we have the vertical overlap layer with the corner already made
       
    elif vo&gt;0:
          # Make the vertical overlap layer
          ver = layer.copy()
          ver.name = "Vertical overlap"
          img.active_layer = layer   # Mind its correct position
          img.add_layer(ver, -1)
          if gradtype==1: ver_mask = ver.create_mask(5)
          else: ver_mask = ver.create_mask(0)
          ver.add_mask(ver_mask)

    else:
       # Nothing to do
       msa_deinit(img)
       return
    
    if vo&gt;0:
       # Rotate and do the vertical tiling
       pdb.gimp_image_rotate(img, 2)
       msa_proc(img, ver, ver_mask, vo, gcontr, gfuzzy, gradtype)
       pdb.gimp_image_rotate(img, 0)
    
    # Deinitialize
    if flatten: img.flatten()
    msa_deinit(img)


register(
    "make_seamless_advanced",
    "Makes seamless textures with some advanced options",
    "",
    "Efenstor",
    "(copyLEFT) Andrey \"Efenstor\" Pivovarov",
    "2013",
    "&lt;Image&gt;/Filters/Map/Make Seamless Advanced...",
    "RGB*, GRAY*",
    [
        (PF_INT, "ho", "Horizontal overlap (px)", 100),
        (PF_INT, "vo", "Vertical overlap (px)", 100),
        (PF_SLIDER, "gcontr", "Gradient contrast", 0, (0, 100, 1)),
        (PF_INT, "gfuzzy", "Gradient fuzziness (px)", 0),
        (PF_RADIO, "gradtype", "Gradient type", 1, (("Simple", 0), ("Intelligent", 1))),
        (PF_TOGGLE, "hipass", "Hi-pass pre-filter", 1),
        (PF_SLIDER, "hpblur", "Hi-pass smoothness\n(0 = auto)", 0, (0, 100, 1)),
        (PF_TOGGLE, "manual", "Manual overlap (only shift and crop)", 0),
        (PF_TOGGLE, "flatten", "Flatten", 1)
    ],
    [],
    make_seamless_advanced)

main()

</pre></body></html>