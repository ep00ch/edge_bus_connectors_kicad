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
import math

import FootprintWizardBase as FPWbase
import PadArray as PA

class PadEdgeConArray(PA.PadArray):
    """ Creates a staggered array of Pads with Z pad naming

                | pad pitch
                |   |
                o   o   o   o     ----
    staggered --> o   o   o   o   -- line_pitch
    line        o   o   o   o
                  o   o   o   o
    """
    def __init__(self, aPad, aPadCount, aLineCount, aLinePitch, aPadPitch,
                        aAlphaName, aAlphaSkip, aFatTraces, aStagger,
                        aCentre=pcbnew.wxPoint(0, 0)):
        """
        @param aPad         Template for all pads
        @param aPadCount    Overall pad count
        @param aLineCount   Number of lines
        @param aLinePitch   distance between lines
        @param aPadPitch    distance between pads
        @param aStagger     X stagger value for all odd lines
        @param aCentre      Center position
        @param aAlphaName   Letters for pad names
        @param aAlphaName   Letters to skip for pad names

        """
        super(PadEdgeConArray, self).__init__(aPad)

        self.padCount = int(aPadCount)
        self.lineCount = int(aLineCount)
        self.linePitch = aLinePitch
        self.padPitch = aPadPitch
        self.stagger = aStagger
        self.centre = aCentre
        self.alphaName = aAlphaName
        self.alphaSkip = aAlphaSkip
        self.fatTrace  = aFatTraces
        self.alphaOffs = ord('@')
        
    def NamingFunction(self, aPadPos):
        # For letter, left to right from front for both rows.
        # For number, left to right, then right to left from front.
        
        if self.alphaName:
            if (aPadPos/self.padCount) >= 1 :
                # Use numbers right to left for back side.
                self.alphaOffs = ord('@') # Reset alpha
                return (aPadPos%self.padCount)+self.firstPadNum
            
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
            if aPadPos >= self.padCount :
                # Continue numbers right to left for back side.
                return self.padCount-(aPadPos-self.padCount)+self.padCount

            return self.firstPadNum + aPadPos

    # relocate the pad and add it as many times as we need
    def AddPadsToModule(self, dc):
        #pin1posX = self.centre.x - ((self.padPitch * (self.padCount // 2 - 1)) + self.stagger) / 2
        pin1posX = self.centre.x - (self.padPitch * (self.padCount - 1)) / 2
        pin1posY = self.centre.y
        dc.SetLineThickness(pcbnew.FromMM(.5))
        
        #BCuSet = pcbnew.LSET(2, pcbnew.B_Cu, pcbnew.B_Mask)

        viaHeight = (self.pad).GetSize().GetHeight()
        zigWidth = (self.padPitch/2)-self.stagger
        zigHeight = viaHeight/1.4 # sq. rt. 2
        zagHeight = viaHeight
        strgtLen = self.linePitch-zigHeight-(zagHeight/2)
        
        posY = pin1posY
        finY = pin1posY + self.linePitch
        
        connPitch = 1.25*self.linePitch

        for linenum in range(0, self.lineCount):
            lineodd = (linenum %2)
            
            if lineodd == 0 :
                dc.SetLayer(pcbnew.F_Cu)
                posY -= connPitch

            for padnum in range(0, self.padCount):
                finX = pin1posX + (self.padPitch * padnum)
                posX = finX + (self.stagger * lineodd)
                pos = dc.TransformPoint(posX, posY)
                
                pad = self.GetPad(padnum == 0, pos)     # in super
                pad.SetName(self.GetName((lineodd*self.padCount)+padnum))
                if linenum > 0 :
                    #dc.SetLayer(pcbnew.B_Cu)
                    if not linenum == self.lineCount-2:
                        pad.SetLayerSet( pcbnew.FlipLayerMask( pad.ConnSMDMask() ))

                self.AddPad(pad)
                
                if lineodd:
                   dc.TransformFlip(pos.x, pos.y+(self.linePitch/2)+(connPitch-(viaHeight/3)),3)
                # Connect TH to finger.
                if self.linePitch > 0 :
                    if str(padnum+1) in self.fatTrace :
                        if lineodd == 0 :
                            dc.SetLayer(pcbnew.F_Cu)
                        else:
                            dc.SetLayer(pcbnew.B_Cu)

                        dc.SetLineThickness(viaHeight)
                        dc.VLine(pos.x, pos.y, (self.linePitch*3.25))    # Down line
                        dc.SetLineThickness(pcbnew.FromMM(.5))

                    elif linenum == 0 :
                        dc.VLine(finX, finY, -(self.linePitch*2.25))    # Down line

                    else :
                        dc.SetLayer(pcbnew.B_Cu)
                        if self.stagger > 0 :
                            dc.VLine(pos.x, pos.y, strgtLen)              # Down line
                            dc.Line(pos.x, pos.y+strgtLen,
                                posX+zigWidth, pos.y+strgtLen+zigHeight) # Diagonal right line
                            dc.VLine(pos.x+zigWidth, pos.y+strgtLen+zigHeight,
                                 zagHeight)                             # Down line
                            dc.Line(pos.x+zigWidth, finY-strgtLen-zigHeight,
                                finX, finY-strgtLen)                    # Diagonal left line
                            dc.VLine(finX, finY, -strgtLen)             # Down line
                        else :
                            p = self.padPitch/2
                            if (p > (viaHeight*2)) :
                                p = viaHeight*2

                            x = self.linePitch
                            #r = (((x**2)/p)+p)/2
                            #a = math.asin(x/r)
                                #dc.Arc((posX-r+p), pos.y + x,
                                #posX, pos.y, a*573)
                            #dc.VLine(posX+p, pos.y+x, connPitch)
                            dc.Line(pos.x, pos.y, pos.x+p, pos.y+x+connPitch)
                            dc.Line(pos.x+p, pos.y+x+connPitch, finX, pos.y+x+connPitch+self.linePitch)
                                    #dc.Arc((pos.x-r+p), pos.y+x+connPitch, finX,
                                    #pos.x+p, pos.y+x+connPitch, a*573)
                if lineodd:
                    dc.PopTransform()

            posY -= self.linePitch

            #if self.stagger:
            #posX-=hPadPitch
            #else:
            #posX+=self.padPitch
            #dc.SetLayer(pcbnew.B_Cu)

class CardEdgeWizard(FPWbase.FootprintWizard):
    padCountKey           = 'pad count'
    alphaNameKey          = 'alpha name'
    alphaSkipKey          = 'skip alpha'
    rowSpacingKey         = 'row spacing'
    padLengthKey          = 'pad length'
    padWidthKey           = 'pad width'
    padPitchKey           = 'pad pitch'
    fatTraceKey           = 'fat traces'
    staggerKey            = 'stagger vias'
    conCountKey           = 'connector count'
    #    pinNames              = "Card_Edge_Connector"
    
    def GetName(self):
        return "Card Edge Connector"

    def GetDescription(self):
        return "Card Edge Connector, Footprint Wizard"

    def GenerateParameterList(self):
        # defaults for a Micromatch package
        self.AddParam("Connectors", self.conCountKey,self.uInteger, 8)

        self.AddParam("Pads", self.padCountKey,     self.uInteger, 43, multiple=1)
        self.AddParam("Pads", self.alphaNameKey,    self.uBool, True)
        self.AddParam("Pads", self.fatTraceKey,     self.uString, "1 2 3 11 16 20 21 22 41 42 43 9 17 24")
        self.AddParam("Pads", self.alphaSkipKey,    self.uString, "GIOQ")

        #and override some of them
        self.AddParam("Pads", self.padWidthKey,     self.uMM, 2.54)
        self.AddParam("Pads", self.padLengthKey,    self.uMM, 10.0)
        self.AddParam("Pads", self.padPitchKey,     self.uMM, 3.96)
        self.AddParam("Pads", self.rowSpacingKey,   self.uMM, 2.54*2)
        self.AddParam("Pads", self.staggerKey,      self.uBool, False)

    def CheckParameters(self):
        pass    # All checks are already taken care of!

    def GetValue(self):
        pad_count = self.parameters["Pads"][self.padCountKey]
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
        return PA.PadMaker(self.module).THRoundPad(pcbnew.FromMM(1.9), pcbnew.FromMM(.9))

    def GetConPad(self):
        """!
        A round non-plated though hole pad (NPTH)
        @param drill: the drill diameter
        """
        pad = PA.PadMaker(self.module).THRoundPad(pcbnew.FromMM(1.9), pcbnew.FromMM(.9))
        pad.SetLayerSet( pad.ConnSMDMask() )
        #pad.SetLayerSet( pad.StandardMask() )

        return pad

    def BuildThisFootprint(self):
        pads = self.parameters["Pads"]
        cons = self.parameters["Connectors"]
        num_cons = cons[self.conCountKey]
        num_pads = pads[self.padCountKey]
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
        #self.draw.SetLayer(pcbnew.F_Cu)
        pad = self.GetFinger()
        #    def __init__(self, aPad, aPadCount, aLineCount, aLinePitch, aPadPitch,
        array = PadEdgeConArray(pad, num_pads, 1, 0, pad_pitch,
                                alpha_name, alpha_skip, "", stagger)
        array.AddPadsToModule(self.draw)
        
        pad_offset_y = (pad_length/2)+row_pitch
        #self.draw.SetLayer(pcbnew.F_Cu)
        pad = self.GetThru()
        #pad = self.GetNPThru()
        array = PadEdgeConArray(pad, num_pads, num_cons*2, row_pitch, pad_pitch,
                                    alpha_name, alpha_skip, fat_traces, stagger,
                                    aCentre=pcbnew.wxPoint(0, -pad_offset_y))
        array.AddPadsToModule(self.draw)
        #self.draw.SetLayer(pcbnew.F_Cu)
        #pad = self.GetConPad()
        #pad = self.GetNPThru()
        #array = PadEdgeConArray(pad, num_pads, num_cons*2, row_pitch, pad_pitch,
        #                       alpha_name, alpha_skip, fat_traces, stagger,
        #                       aCentre=pcbnew.wxPoint(0, -pad_offset_y))
                                #array.AddPadsToModule(self.draw)

        ## Draw connector outlineChassis
        width =  (num_pads * pad_pitch)
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
