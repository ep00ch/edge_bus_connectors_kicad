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

class PadEdgeConArray(PA.PadArray):
    """ Creates an 2 sided edge connector and an array of Pads with
        edge connector pad naming (letters on one side and numbers on the other).
        Options include:
            easily create a backplane by changing the connector count;
            numeric or alpha numeric numbering;
            stagger the vias;
            fat traces, connected to both sides for power signals.

    """
    def __init__(self, aPad, aPosCount, aConnCount, aLinePitch, aPadPitch,
                        aAlphaName, aAlphaSkip, aFatTraces, aStagger, aPreferBot,
                        aCentre=pcbnew.wxPoint(0, 0)):
        """
        @param aPad         Template for all pads
        @param aPosCount    Pad Position count
        @param aConnCount   Number of connectors
        @param aLinePitch   distance between lines
        @param aPadPitch    distance between pads
        @param aStagger     X stagger value for all odd lines
        @param aPreferBot   Prefer traces and pads on bottom
        @param aCentre      Center position
        @param aAlphaName   Letters for pad names
        @param aAlphaName   Letters to skip for pad names

        """
        super(PadEdgeConArray, self).__init__(aPad)

        self.posCount = int(aPosCount)
        self.connCount = int(aConnCount)
        self.linePitch = aLinePitch
        self.padPitch = aPadPitch
        self.stagger = aStagger
        self.centre = aCentre
        self.alphaName = aAlphaName
        self.alphaSkip = aAlphaSkip
        self.fatTrace  = aFatTraces
        self.alphaOffs = ord('@')
        self.preferBot = aPreferBot


    def NamingFunction(self, aPadPos):
        # For letter, left to right from front for both rows.
        # For number, left to right, then right to left from front.
        
        if self.alphaName:
            if aPadPos >= self.posCount :
                # Use numbers right to left for back side.
                return (aPadPos%self.posCount)+self.firstPadNum
            
            if aPadPos == 0 :
                # Reset the alpha offset for the new line
                self.alphaOffs = ord('@') # Reset alpha
                
            padord = self.firstPadNum + aPadPos + self.alphaOffs
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
            if aPadPos >= self.posCount :
                # Continue numbers right to left for back side.
                return self.posCount-(aPadPos-self.posCount)+self.posCount

            return self.firstPadNum + aPadPos

    # relocate the pad and add it as many times as we need
    def AddPadsToModule(self, dc):
        #pin1posX = self.centre.x - ((self.padPitch * (self.posCount // 2 - 1)) + self.stagger) / 2
        pin1posX = self.centre.x - (self.padPitch * (self.posCount - 1)) / 2
        pin1posY = self.centre.y
        dc.SetLineThickness(pcbnew.FromMM(.5))
        
        connPitch = 3.25*self.linePitch

        maxrange = 2 if self.linePitch else 1
        for sidenum in range(0, maxrange):
            posY = pin1posY

            if sidenum == 0 :
                dc.SetLayer(pcbnew.F_Cu)
            elif sidenum > 0:
                posY -=self.linePitch
                dc.SetLayer(pcbnew.B_Cu)
            finY = posY + connPitch

            for connum in range(0, self.connCount):
                for padnum in range(0, self.posCount):
                    
                    if sidenum == 0 and self.preferBot and connum > 0 :
                        dc.SetLayer(pcbnew.B_Cu)
                    
                    finX = pin1posX + (self.padPitch * padnum)
                    posX = finX + (self.stagger * sidenum)
                    pos = dc.TransformPoint(posX, posY)
                    
                    pad = self.GetPad(padnum == 0, pos)     # in super
                    pad.SetName(self.GetName(( sidenum * self.posCount)+padnum))
                    self.AddPad(pad)

                    viaWidth = pad.GetSize().GetWidth()
                    viaHole = pad.GetDrillSize().GetWidth()
                    wideWidth = int( viaHole + (( viaWidth - viaHole)/2) )
                    # Draw buses only for the connector pads
                    if self.linePitch > 0 :
                        # Connect power with fat traces
                        if str(padnum+1) in self.fatTrace :
                            viaHole = pad.GetDrillSize().GetWidth()
                            if sidenum == 0:
                                dc.SetLayer(pcbnew.F_Cu)
                            dc.SetLineThickness( wideWidth )
                            if connum == 0:
                                dc.VLine(pos.x, pos.y, (int(self.linePitch*sidenum)+(self.linePitch*2)))
                            else:
                                dc.VLine(pos.x, pos.y, connPitch)    # Down line
                            dc.SetLineThickness(pcbnew.FromMM(.5))
                            
                        # Connect to front finger with shorter line.
                        elif connum == 0 and sidenum == 0:
                            dc.VLine(pos.x, pos.y, self.linePitch*2)    # Down line
                        # Connect each pad in a bus.
                        else :
                            if self.stagger > 0 :
                                if sidenum and connum == 0:
                                    dc.VLine(pos.x, pos.y, self.linePitch) # Down line
                                    dc.Line(pos.x, pos.y+self.linePitch,
                                        pos.x-self.stagger, pos.y+self.linePitch+(connPitch-self.linePitch))
                                else:
                                    dc.VLine(pos.x, pos.y, connPitch) # Down line

                            else :
                                if sidenum:
                                    # Flip the trace so it does not interfere.
                                    dc.TransformFlip(pos.x, (pos.y+connPitch/2),3)
                                xp = self.padPitch/2
                                if (xp > viaWidth * 2) :
                                    # Limit for really wide pad pitches
                                    xp = viaWidth*2

                                yp = self.linePitch
                                w = (viaWidth/2)
                                dc.Line(pos.x, pos.y, pos.x+xp, pos.y+connPitch-yp-w)
                                dc.VLine(pos.x+xp, pos.y+connPitch-yp-w, viaWidth)
                                dc.Line(pos.x+xp, pos.y+connPitch-yp+w, finX, pos.y+connPitch)
                                if sidenum:
                                    dc.PopTransform()

                posY -= connPitch



class CardEdgeWizard(FPWbase.FootprintWizard):
    conCountKey           = 'connector count'
    conBottomKey          = 'prefer bottom traces'
    padCountKey           = 'position count'
    alphaNameKey          = 'alpha name'
    alphaSkipKey          = 'skip alpha'
    rowSpacingKey         = 'row spacing'
    padLengthKey          = 'pad length'
    padWidthKey           = 'pad width'
    padPitchKey           = 'pad pitch'
    fatTraceKey           = 'fat traces'
    staggerKey            = 'stagger vias'
    #    pinNames              = "Card_Edge_Connector"
    
    def GetName(self):
        return "Card Edge Connector"

    def GetDescription(self):
        return "Card Edge Connector, Footprint Wizard"

    def GenerateParameterList(self):
        # defaults for a EXORbus
        self.AddParam("Connectors", self.conCountKey,self.uInteger, 8)
        self.AddParam("Connectors", self.conBottomKey,self.uBool, False)

        self.AddParam("Pads", self.conCountKey,     self.uInteger, 43, multiple=1)
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
        pad_count = self.parameters["Pads"][self.conCountKey]
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
        return PA.PadMaker(self.module).THRoundPad(pcbnew.FromMils(80), pcbnew.FromMils(52))

    def GetConPad(self):
        """!
        A round non-plated though hole pad (NPTH)
        @param drill: the drill diameter
        """
        pad = PA.PadMaker(self.module).THRoundPad(pcbnew.FromMils(80), pcbnew.FromMils(52))
        #pad.SetLayerSet( pad.ConnSMDMask() )
        pad.SetLayerSet( pad.StandardMask() )

        return pad

    def BuildThisFootprint(self):
        pads = self.parameters["Pads"]
        cons = self.parameters["Connectors"]
        num_cons = cons[self.conCountKey]
        pref_bottom = cons[self.conBottomKey]

        num_pos = pads[self.conCountKey]
        pad_length = pads[self.padLengthKey]
        row_pitch = pads[self.rowSpacingKey]
        pad_pitch = pads[self.padPitchKey]
        pad_width = pads[self.padWidthKey]
        fat_traces= pads[self.fatTraceKey].split()
        stagger = (pad_pitch/2) if pads[self.staggerKey] else 0

        alpha_name = pads[self.alphaNameKey]
        alpha_skip = pads[self.alphaSkipKey]
        
        # Use value to fill the modules description
        desc = self.GetValue()
        self.module.SetDescription(desc)
        self.module.SetAttributes(1)

        # add in the pads
        pad = self.GetFinger()
        #    def __init__(self, aPad, aPosCount, aconnCount, aLinePitch, aPadPitch,
        array = PadEdgeConArray(pad, num_pos, 1, 0, pad_pitch,
                                alpha_name, alpha_skip, "", stagger, False)
        array.AddPadsToModule(self.draw)
        
        #pad_offset_y = (pad_length/2)+(row_pitch*1.5)
        pad_offset_y = (pad_length/2)+(row_pitch*2)

        pad = self.GetThru()
        array = PadEdgeConArray(pad, num_pos, num_cons, row_pitch, pad_pitch,
                                    alpha_name, alpha_skip, fat_traces, stagger,
                                    pref_bottom,
                                    aCentre=pcbnew.wxPoint(0, -pad_offset_y))
        array.AddPadsToModule(self.draw)

        ## Draw connector outlineChassis
        width =  (num_pos * pad_pitch)
        height = pcbnew.FromMM(5)
        #
        #self.draw.SetLineThickness( pcbnew.FromMM( 0.12 ) ) #Default per KLC F5.1 as of 12/2018
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
