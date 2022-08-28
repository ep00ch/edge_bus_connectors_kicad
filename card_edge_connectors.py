#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#define

from __future__ import division
import pcbnew

import FootprintWizardBase as FPWbase
import PadArray as PA

class PadBusConArray(PA.PadGridArray):
    alphaName = True
    alphaSkip = ""
    alphaOffs = 0
    
    """ Creates an 2 sided edge connector or an array of through hole Pads with
        edge connector pad naming (letters on one side and numbers on the other).
        Options include:
            easily create a backplane by changing the connector count;
            numeric or alpha numeric numbering;
            fat traces, connected to both sides for power signals.
    @param pad: the prototypical pad of the array
    @param nx: number of pads in x-direction
    @param ny: number of pads in y-direction
    @param px: pitch in x-direction
    @param py: pitch in y-direction
    @param centre: array centre point
    """
    def setNaming(self, alpha_name, alpha_skip):
        self.alphaName = alpha_name
        self.alphaSkip = alpha_skip
    
    
    def NamingFunction(self, x, y):
        """
        # For number, left to right, then right to left from front.
        @param x: the pad x index
        @param y: the pad y index
        """
        if self.alphaName:
            if y or x >= self.nx: #x >= self.nx :
                # Use numbers left to right for back side.
                return (x%self.nx)+self.firstPadNum
            
            if x == 0 :
                # Reset the alpha offset for the new line
                self.alphaOffs = ord('@') # Reset alpha
                
            padord = self.firstPadNum + x + self.alphaOffs
            # Use numbers after all letters used.
            if padord > ord('z') :
                return padord - ord('z')

            # Skip the indicated letters upper and lower.
            while chr(padord).lower() in self.alphaSkip.lower():
                self.alphaOffs+=1
                padord+=1

            # Jump to lower case after all caps used.
            if padord == ord('Z') :
                self.alphaOffs+=6
            
            return str(chr(padord))
        else :
            # Return the number.
            return self.firstPadNum + (self.nx*y + x)

    # Add bus lines as many times as we need
    def AddBusToModule(self, dc, connPitch, fatTraces, preferBot, staggerPad, toEdge ):
        """
        # Add bus wires connecting the connetors and card edge.
        @param dc: the drawing context
        @param connPitch: the pitch of the connectors
        @param fatTraces: array of pin names that need fat power traces connecting both sides of the connector
        @param preferBot: put the bus wires on the bottom. fat traces remain on top and bottom
        @param toEdge: set to true if this is the first connector, closest to card edge
        """
        pin1posX = self.centre.x - self.px * (self.nx - 1) / 2
        pin1posY = self.centre.y - self.py * (self.ny - 1) / 2
 
        dc.SetLineThickness(pcbnew.FromMM(.5))
        
        for row in range(0, self.ny):
            # move vertically down through rows
            posY = pin1posY + (row * self.py)

            for padnum in range(0, self.nx):
                if row == 0 :
                    dc.SetLayer(pcbnew.B_Cu)
                    stagger = 0

                else :
                    dc.SetLayer(pcbnew.F_Cu)
                    stagger = staggerPad
                    
                posX = pin1posX + (self.px * padnum) + stagger
                pos = pcbnew.wxPoint(posX, posY)
                
                viaWidth = self.pad.GetSize().GetWidth()
                viaHole = self.pad.GetDrillSize().GetWidth()
                wideWidth = int( viaHole + (( viaWidth - viaHole)/2) )
                
                # Connect power with straight, wider traces
                if str(padnum+1) in fatTraces :
                    dc.SetLineThickness( wideWidth )
                    
                    if row and toEdge:
                        # Connect to back finger with shorter line.
                        dc.Line(pos.x, pos.y, pos.x-stagger, pos.y+connPitch)

                    else :
                        # Connect to back finger with down line.
                        dc.VLine(pos.x, pos.y, connPitch)    # Down line
                    
                    dc.SetLineThickness(pcbnew.FromMM(.5))

                elif row and toEdge:
                    # Connect to back finger with shorter line.
                    dc.Line(pos.x, pos.y, pos.x-stagger, pos.y+connPitch)

                # Connect to next pad with a bent line.
                else :
                    if preferBot :
                        dc.SetLayer(pcbnew.B_Cu)
                        
                    if row :
                        # Flip the trace so it does not interfere.
                        dc.TransformFlip(pos.x, (pos.y+connPitch/2),3)
                        
                    if staggerPad :
                        xp = 0
                    else :
                        # Limit arch size for really wide pad pitches
                        xpMax = viaWidth*2
                        xpMin = self.px/2
                        xp =  xpMin if (xpMin < xpMax) else xpMax
                    yp = self.py
                    
                    w = (viaWidth/2)
                    #Line from pad to top of area between pads
                    dc.Line(pos.x, pos.y, pos.x-xp, pos.y+yp-w)
                    #Line from top to bottom of area between lower pad
                    dc.VLine(pos.x-xp, pos.y+yp-w, viaWidth)
                    #Line bottom of area between pads to lower connector
                    dc.Line(pos.x-xp, pos.y+yp+w, pos.x, pos.y+connPitch)

                    if row :
                        dc.PopTransform()   # remove the TransformFlip


class CardEdgeWizard(FPWbase.FootprintWizard):
    conCountKey           = 'connector count'
    conSpacingKey         = 'connector spacing'
    conBottomKey          = 'prefer bottom traces'
    posCountKey           = 'position count'
    alphaNameKey          = 'alpha name'
    alphaSkipKey          = 'skip alpha'
    rowSpacingKey         = 'row spacing'
    padLengthKey          = 'pad length'
    padWidthKey           = 'pad width'
    padPitchKey           = 'pad pitch'
    fatTraceKey           = 'fat traces'
    staggerKey            = 'stagger vias'
    #    pinNames              = "Card_Edge_Connector"
    padNames = ''
    
    def GetName(self):
        return "Card Edge Connector"

    def GetDescription(self):
        return "Card Edge Connector, Footprint Wizard"

    def GenerateParameterList(self):
        # defaults for a EXORbus
        self.AddParam("Connectors", self.conCountKey,self.uInteger, 8)
        self.AddParam("Connectors", self.conSpacingKey,self.uMM, 19.05)
        self.AddParam("Connectors", self.conBottomKey,self.uBool, False)

        self.AddParam("Pads", self.posCountKey,     self.uInteger, 43, multiple=1)
        self.AddParam("Pads", self.alphaNameKey,    self.uBool, True)
        self.AddParam("Pads", self.fatTraceKey,     self.uString, "1 2 3 11 16 20 21 22 41 42 43 9 17 24")
        self.AddParam("Pads", self.alphaSkipKey,    self.uString, "GIOQ")

        self.AddParam("Pads", self.padWidthKey,     self.uMM, 2.54)
        self.AddParam("Pads", self.padLengthKey,    self.uMM, 8.0)
        self.AddParam("Pads", self.padPitchKey,     self.uMM, 3.96)
        self.AddParam("Pads", self.rowSpacingKey,   self.uMM, 2.54*2)
        self.AddParam("Pads", self.staggerKey,      self.uBool, False)

    def CheckParameters(self):
        pass    # All checks are already taken care of!

    def GetValue(self):
        pad_count = self.parameters["Pads"][self.posCountKey]
        return "%s-%d" % ("Card_Edge_Connector", pad_count)

    def GetFinger(self):
        pad_length = self.parameters["Pads"][self.padLengthKey]
        pad_width  = self.parameters["Pads"][self.padWidthKey]
        pad = PA.PadMaker(self.module).SMDPad(pad_length,
                            pad_width, shape=pcbnew.PAD_SHAPE_RECT)
        #pad.SetAttribute(pcbnew.PAD_ATTRIB_STANDARD)
        pad.SetAttribute( pcbnew.PAD_ATTRIB_CONN )
        pad.SetLayerSet( pad.StandardMask() )
        #pad.SetLayerSet( pad.ConnSMDMask() )
        #pad.SetLayerSet( pad.SMDMask() )
        return pad

    def GetThru(self):
        return PA.PadMaker(self.module).THRoundPad(pcbnew.FromMils(70.86614), pcbnew.FromMils(35.43307))
        #return PA.PadMaker(self.module).THRoundPad(pcbnew.FromMils(80), pcbnew.FromMils(52))

    def GetConPad(self):
        """!
        A round non-plated though hole pad (NPTH)
        @param drill: the drill diameter
        """
        pad = PA.PadMaker(self.module).THRoundPad(pcbnew.FromMils(90), pcbnew.FromMils(52))
        pad.SetLayerSet( pad.StandardMask() )

        return pad

    def BuildThisFootprint(self):
        pads = self.parameters["Pads"]
        cons = self.parameters["Connectors"]
        num_cons = cons[self.conCountKey]
        con_pitch = cons[self.conSpacingKey]
        pref_bottom = cons[self.conBottomKey]

        num_pos = pads[self.posCountKey]
        pad_length = pads[self.padLengthKey]
        row_pitch = pads[self.rowSpacingKey]
        pad_pitch = pads[self.padPitchKey]
        pad_width = pads[self.padWidthKey]
        fat_traces= pads[self.fatTraceKey].split()
        stagger = (pad_pitch/2) if pads[self.staggerKey] else 0
        
        # Use value to fill the modules description
        desc = self.GetValue()
        self.module.SetDescription(desc)
        self.module.SetAttributes(1)

        # add in the finger pads
        pad = self.GetFinger()

        array = PadBusConArray(pad, num_pos, 1, pad_pitch, 0)
        array.setNaming(pads[self.alphaNameKey], pads[self.alphaSkipKey])
        array.AddPadsToModule(self.draw)
        
        # add in the connector pads
        pad = self.GetConPad()
        num_rows = 2 if num_cons else 1
        #array = PA.PadGridArray(pad, num_pos, num_rows, pad_pitch, row_pitch)

        #self.draw.ResetTransform()
        
        if (stagger):
            array = PadBusConArray(pad, num_pos, 2, pad_pitch, row_pitch)

            array1 = PadBusConArray(pad, num_pos, 1, pad_pitch, 0, pcbnew.wxPoint(0, -row_pitch/2))
            array1.setNaming(0, pads[self.alphaSkipKey])
            array1.firstPadNum = num_pos+1
            
            array2 = PadBusConArray(pad, num_pos, 1, pad_pitch, 0, pcbnew.wxPoint(stagger, row_pitch/2))
            array2.setNaming(pads[self.alphaNameKey], pads[self.alphaSkipKey])
            
            for connum in range(0, num_cons):
                    self.draw.TransformTranslate(0, -con_pitch, 1)
                    
                    array1.AddPadsToModule(self.draw)
                    array2.AddPadsToModule(self.draw)

                    array.AddBusToModule(self.draw, con_pitch, fat_traces,
                        cons[self.conBottomKey], stagger, (connum == 0))
            
            self.draw.ResetTransform()

        else :
            if (num_cons == 0 ):
                # if no bus connectors, at least add through-hole connections to the front pads
                array = PadBusConArray(pad, num_pos, 1, pad_pitch, 0)
                num_cons = 1
            else :
                array = PadBusConArray(pad, num_pos, 2, pad_pitch, row_pitch)
                                    
            array.setNaming(pads[self.alphaNameKey], pads[self.alphaSkipKey])
        
            for connum in range(0, num_cons):
                # Move to next connector.
                self.draw.TransformTranslate(0, -con_pitch, 1)

                # Put lettered pads on bottom.
                self.draw.TransformFlip(array.centre.x, array.centre.y, 2)
                array.AddPadsToModule(self.draw)
                self.draw.PopTransform()
            
                # Add the bus lines.
                array.AddBusToModule(self.draw, con_pitch, fat_traces,
                    cons[self.conBottomKey], stagger, (connum == 0))

            self.draw.ResetTransform()


        ## Draw connector outlineChassis
        width =  (num_pos * pad_pitch)
        height = pcbnew.FromMM(5)
        #
        #Default per KLC F5.1 as of 12/2018
        #self.draw.SetLineThickness( pcbnew.FromMM( 0.12 ) )
        #
        ## Left part
        ##  --
        ##  |
        ##  ----
        #self.draw.Polyline([(-width/2 + pcbnew.FromMM(0.5), -height/2),
        #                    (-width/2, -height/2),
        #                    (-width/2, height/2),
        #                    (-width/2 + pcbnew.FromMM(0.5) + padPitch / 2, height/2)])
        #
        #if drawWithLock :
        #    # Right part with pol slot
        #    #  ----
        #    #     [
        #    #    --
        #    self.draw.Polyline([(width/2 - pcbnew.FromMM(0.5) - padPitch / 2, -height/2),
        #                        (width/2,                                     -height/2),
        #                        (width/2,                                     -height/2 + pcbnew.FromMM(1.25)),
        #                        (width/2 - pcbnew.FromMM(0.7),                -height/2 + pcbnew.FromMM(1.25)),
        #                        (width/2 - pcbnew.FromMM(0.7),                 height/2 - pcbnew.FromMM(1.25)),
        #                        (width/2,                                      height/2 - pcbnew.FromMM(1.25)),
        #                        (width/2,                                      height/2),
        #                        (width/2 - pcbnew.FromMM(0.5),                 height/2)])
        #else:
        #    # Right part without pol slot
        #    #  ----
        #    #     |
        #    #    --
        #    self.draw.Polyline([(width/2 - pcbnew.FromMM(0.5) - padPitch / 2, -height/2),
        #                        (width/2,                                     -height/2),
        #                        (width/2,                                      height/2),
        #                        (width/2 - pcbnew.FromMM(0.5),                 height/2)])
        #
        # Courtyard
        self.draw.SetLayer(pcbnew.F_CrtYd)
        self.draw.SetLineThickness(pcbnew.FromMM(0.05))
        boxW = width                +(pad_pitch-pad_width)
        boxH = pad_length + pcbnew.FromMM(2)

        # Round courtyard positions to 0.1 mm, rectangle will thus land on a 0.05mm grid
        pcbnew.PutOnGridMM(boxW, pcbnew.FromMM(0.10))
        pcbnew.PutOnGridMM(boxH, pcbnew.FromMM(0.10))
        self.draw.Box(0,  -pcbnew.FromMM(1), boxW, boxH)

        # reference and value
        text_size = pcbnew.FromMM(1.0)  # According KLC
        text_offset = row_pitch

        self.draw.Value(0, -1.5*text_offset, text_size)
        self.draw.Reference(0, -2.5*text_offset, text_size)

CardEdgeWizard().register()
