#    https://launchpad.net/wxbanker
#    smoothsizer.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
#
#    This file is part of wxBanker.
#
#    wxBanker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    wxBanker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with wxBanker.  If not, see <http://www.gnu.org/licenses/>.

"""
A Sizer mixin that allows Insertions (Add/Insert/Prepend), Hides amd Removals
to be done "smoothly", by gradually adding or removing the necessary space.

Smooth methods supported: Insert, Add, Prepend, Hide, Remove

@author     Mike Rooney
@date       08/06/2007
@version    0.3

Changes:
--------
0.3
 - added a SmoothRemove method in the Mixin
0.2
 - SmoothHide no longer changes the number of children in the sizer temporarily
 - added a SmoothStaticBoxSizer
 - added a Smooth property
 - various code cleanup and commenting
0.1
 - initial implementation with ability to smoothly Insert/Add/Prepend, and Hide items
 - an example SmoothBoxSizer

Todo:
 - a smooth Show
 - a SmoothAdapter of some kind?
 - verify that smooth insert/remove work with smooth=False
"""
import wx

class SmoothSizerMixin:
    """
    This class is a mixin to allow items to be "smoothly" added/removed/hidden
    to a sizer. When using a sizer with this mixin, smooth actions will
    be the default.

    To instantly perform an action, pass smooth=False into
    the Add/Prepend/Insert/Hide/Remove call.
    """
    def __init__(self, delay=200, increment=15):
        self._delay = delay/1000.0
        self._increment = increment/1000.0
        self._actives = {}
        self._isSmooth = True

    def GetObject(self, sizerItem):
        """
        This method gets the actual object in the sizer, given a SizerItem.
        You would think this would be a little easier.
        """
        if sizerItem.IsWindow():
            return sizerItem.Window
        elif sizerItem.IsSizer():
            return sizerItem.Sizer
        else:
            return sizerItem.Spacer

    def GetSmooth(self):
        return self._isSmooth

    def SetSmooth(self, boolval):
        self._isSmooth = boolval

    def GetDelay(self):
        return self._delay

    def SetDelay(self, delay):
        self._delay = delay

    def GetIncrement(self):
        return self._increment

    def SetIncrement(self, increment):
        self._increment = increment

    def Prepend(self, item, *args, **kwargs):
        return self.Insert(0, item, *args, **kwargs)

    def Add(self, item, *args, **kwargs):
        return self.Insert(len(self.GetChildren()), item, *args, **kwargs)

    def GetMyPos(self, index):
        return self._actives[index][0]

    def GetMyDelay(self, index):
        return self._actives[index][2]

    def GetMyIncrement(self, index):
        return self._actives[index][3]

    def LayoutProper(self):
        """
        Attempt a layout of one level up, since we may need more or less space
        to look proper.

        Attempts to Layout the Parent of the containing window first, but if
        None is found it settles for the containing window.
        """
        self.Layout() #not sure why this is necessary first but it is.
        parentWin = self.GetContainingWindow()
        if parentWin:
            if parentWin.Parent:
                parentWin.Parent.Layout()
            else:
                parentWin.Layout()

    def SmoothInsertOrig(self, item, prop=0, flag=0, border=0, userData=None, expandIn=(1, 1), smooth=None, index=-1, spacer=None, pixels=None):
        """
        This method is the heart of the mixin. Initially it creates a boxsizer and inside it puts a spacer
        (initially (0,0)), followed by the actual item to insert. It is done this way so that the item
        is always a child of this sizer, but the length of the sizer is not "inflated" temporarily by containing
        both a spacer and the item.

        It then checks if the space it has allocated for the item via the spacer is enough for the control
        (or if the insertion is not smooth). If either of these are true, it detaches the subsizer
        and adds the item to THIS sizer appropriately based on *args and **kwargs.

        If the spacer is not yet large enough to accomodate the item, it increases the dimensions
        of the sizer and tells wx to call it again according to the specified increment time, upon
        which this process will repeat.

        A bunch of this logic is to handle multiple insertions occurring at once, which is done
        using the _actives list. This keeps track of the position in the sizer that we are modifying
        (which will change if something else is inserted before us while we are inserting), and how
        much space we have currently allocated.
        """
        if smooth is None:
            smooth = self.GetSmooth()

        if spacer is None: #this is our first time here
            #figure out the position of the item
            #pos = self.GetChildren().index(sizerItem) #why doesn't this work
            for i, sitem in enumerate(self.Children):
                if self.GetObject(sitem) is self.GetObject(sizerItem):
                    pos = i; break

            index = int(wx.NewId()) #okay way to get unique id?
            self._actives[index] = [pos, [0, 0], self.Delay, self.Increment, "I"]

            #we are going to be temporarily inserting the item to get its size, so don't show it
            if self.GetContainingWindow():
                self.GetContainingWindow().Freeze()

            #create a gridsizer
            sizer = wx.BoxSizer()
            #add the spacer and item
            spacer = sizer.AddSpacer((0,0))
            sizer.Add(self.GetObject(self.GetItem(pos)))
            #calculate the size of the item
            sizer.Layout()
            space = pixels = [int(expandBool)*size for expandBool, size in zip(expandIn, item.Size)]
            #now hide it
            sizer.Hide(item)
            #and put the temporary sizer where the item will eventually go
            wx.Sizer.Insert(self, pos, sizer)

            if self.GetContainingWindow():
                self.GetContainingWindow().Thaw()

            #if there is a pending insertion after us, they will have their index off by one now
            #so we need to increment all indexes equal to or after us by one
            for i, data in self._actives.items():
                if i is not index and data[0] >= pos:
                    self._actives[i][0] += 1
        else:
            pos = self.GetMyPos(index)
            space = self._actives[index][1]

        #a Hide will set our space to None if this insertion has been "cancelled" by a Hide on the same item
        if space is None:
            #wx.Sizer.Detach(self, pos)
            del self._actives[index]
            return

        #figure out the new size of the spacer
        iters = self.GetMyDelay(index)/self.GetMyIncrement(index)
        offset = [size/iters for size in pixels]
        self._actives[index][1][0] += offset[0]
        self._actives[index][1][1] += offset[1]
        space = self._actives[index][1]

        #now either add the control if we have created enough space, or add a bigger spacer if not
        if not smooth or space > pixels:
            #detach the temporary sizer, and add and show the actual item
            wx.Sizer.Detach(self, pos)
            result = wx.Sizer.Insert(self, pos, item, prop, flag, border, userData)
            self.Show(item)
            #remove ourselves from the dictionary, we don't want it to keep increasing
            del self._actives[index]
        else: #not enough space yet, keep enlarging spacer
            spacer.SetSpacer(space)
            result = wx.CallLater(self.Increment*1000, self.SmoothInsert, pos, item, prop, flag, border, userData, expandIn, smooth, index, spacer, pixels)

        #layout each iteration
        self.LayoutProper()

        return result

    def SmoothShow(self, item, pixels=None, smooth=None, index=-1, spacer=None, callback=None, *args, **kwargs):
        """
        This method smoothly (by default) adds an item to a sizer.

        It does this by first hiding the item, and then creating a spacer the same size as the
        item was. Then each iteration it reduces the size of the spacer until it is (0,0), at which
        point it detaches the spacer and is done.
        """
        if smooth is None:
            smooth = self.GetSmooth()

        if spacer is None: #this is our first time here
            #if the window is already hidden, just return True that it was found/hidden
            sizerItem = self.GetItem(item)
            if sizerItem.IsShown(): ##X
                return True

            #figure out the position of the item
            #pos = self.GetChildren().index(sizerItem) #why doesn't this work
            for i, sitem in enumerate(self.Children):
                if self.GetObject(sitem) is self.GetObject(sizerItem):
                    pos = i; break

            #we know it is not shown, so grab the size (how much space we need to hide) ###X
            if self.GetContainingWindow(): self.GetContainingWindow().Freeze()
            wx.Sizer.Show(self, item)
            self.Layout()
            pixels = self.GetItem(item).Size
            #print pixels
            wx.Sizer.Hide(self, item)
            if self.GetContainingWindow(): self.GetContainingWindow().Thaw()

            #grab these now before we change anything
            sProp, sFlag, sBorder, sUserData = sizerItem.Proportion, sizerItem.Flag, sizerItem.Border, sizerItem.UserData

            #add ourselves to the list of actives
            index = int(wx.NewId()) #okay way to get unique id?
            self._actives[index] = [pos, [0,0], self.Delay, self.Increment, "I"] ##X

            for i, data in self._actives.items():
                #if there is a pending action on the current item already:
                if i is not index and data[0] == pos:
                    if data[4] == "H": ###
                        #we are being told to hide an item which is in the process of being inserted!
                        #tell it to stop, and use the current space it has allocated
                        self._actives[index][1] = self._actives[i][1]
                        self._actives[i][1] = None
                    elif data[4] == "I": ###
                        #we are being told to show an item, which is already being shown. that's silly.
                        #remove ourselves, return, and let the previous show continue
                        del self._actives[index]
                        return True
                    else:
                        raise Exception("Unable to identify an entry in my dictionary!")

            #we CAN'T change the number of items in the sizer, the user may depend on it
            #hide the item initially
            #wx.Sizer.Hide(self, item, *args, **kwargs) ## not necessary for a show but not harmful either
            #detach it from this sizer, replace it with a sizer with the item and the spacer,
            #so as not to change the number of items
            itemObj = self.GetObject(self.Children[pos])
            wx.Sizer.Detach(self, pos)
            tempSizer = wx.BoxSizer()
            #add the item
            tempSizer.Add(itemObj, 1, wx.EXPAND)
            #add the spacer which we will reduce to nothing
            spacer = tempSizer.AddSpacer(pixels)
            #now add the sizer, mimicking the original item
            wx.Sizer.Insert(self, pos, tempSizer, sProp, sFlag, sBorder, sUserData)

        #figure out the new size of the spacer
        iters = self.GetMyDelay(index)/self.GetMyIncrement(index)
        offset = [size/iters for size in pixels] ## multiple by -1 when appropriate
        self._actives[index][1][0] += offset[0]
        self._actives[index][1][1] += offset[1]
        space = self._actives[index][1]
        print tuple(space), pixels, tuple(space) > tuple(pixels)

        #now either remove the spacer if we have removed enough space, or remove more space if not
        if not smooth or tuple(space) > tuple(pixels): ## space > pixels
            print 1
            #grab the temp sizer
            tempSizerItem = self.Children[self.GetMyPos(index)]
            tempSizer = tempSizerItem.Sizer
            realItemObj = self.GetObject(tempSizer.Children[0])
            #detach the item from it
            tempSizer.Detach(0)
            #add the item back to THIS sizer
            wx.Sizer.Insert(self, self.GetMyPos(index), realItemObj, tempSizerItem.Proportion, tempSizerItem.Flag, tempSizerItem.Border, tempSizerItem.UserData)
            #and remove the temp sizer
            wx.Sizer.Remove(self, tempSizer)
            #remove ourselves from the dictionary, so it doesn't get large
            del self._actives[index]
            wx.Sizer.Show(self, item)
            #if there is a callback, call it!
            if callback:
                callback()
        else: #still space left, reduce size of spacer
            print 0
            spacer.SetSpacer(space)
            result = wx.CallLater(self.Increment*1000, self.SmoothShow, item, pixels, smooth, index, spacer, callback, *args, **kwargs) ##X

        #layout each iteration
        self.LayoutProper()

    def SmoothHide(self, item, pixels=None, smooth=None, index=-1, spacer=None, callback=None, *args, **kwargs):
        """
        This method smoothly (by default) removes an item from a sizer.

        It does this by first hiding the item, and then creating a spacer the same size as the
        item was. Then each iteration it reduces the size of the spacer until it is (0,0), at which
        point it detaches the spacer and is done.
        """
        if smooth is None:
            smooth = self.GetSmooth()

        if spacer is None: #this is our first time here
            #if the window is already hidden, just return True that it was found/hidden
            sizerItem = self.GetItem(item)
            if not sizerItem.IsShown(): ##
                return True

            #figure out the position of the item
            #pos = self.GetChildren().index(sizerItem) #why doesn't this work
            for i, sitem in enumerate(self.Children):
                if self.GetObject(sitem) is self.GetObject(sizerItem):
                    pos = i; break

            #we know it is shown, so grab the size (how much space we need to hide)
            pixels = sizerItem.Size
            #grab these now before we change anything
            sProp, sFlag, sBorder, sUserData = sizerItem.Proportion, sizerItem.Flag, sizerItem.Border, sizerItem.UserData

            #add ourselves to the list of actives
            index = int(wx.NewId()) #okay way to get unique id?
            self._actives[index] = [pos, pixels, self.Delay, self.Increment, "H"] ##

            for i, data in self._actives.items():
                #if there is a pending action on the current item already:
                if i is not index and data[0] == pos:
                    if data[4] == "I": ###
                        #we are being told to hide an item which is in the process of being inserted!
                        #tell it to stop, and use the current space it has allocated
                        self._actives[index][1] = self._actives[i][1]
                        self._actives[i][1] = None
                    elif data[4] == "H": ###
                        #we are being told to hide an item, which is already being hidden. that's silly.
                        #remove ourselves, return, and let the previous hide continue
                        del self._actives[index]
                        return True
                    else:
                        raise Exception("Unable to identify an entry in my dictionary!")

            #we CAN'T change the number of items in the sizer, the user may depend on it
            #hide the item initially
            wx.Sizer.Hide(self, item, *args, **kwargs) ## not necessary for a show but not harmful either
            #detach it from this sizer, replace it with a sizer with the item and the spacer,
            #so as not to change the number of items
            itemObj = self.GetObject(self.Children[pos])
            wx.Sizer.Detach(self, pos)
            tempSizer = wx.BoxSizer()
            #add the item
            tempSizer.Add(itemObj, 1, wx.EXPAND)
            #add the spacer which we will reduce to nothing
            spacer = tempSizer.AddSpacer(pixels)
            #now add the sizer, mimicking the original item
            wx.Sizer.Insert(self, pos, tempSizer, sProp, sFlag, sBorder, sUserData)

        #figure out the new size of the spacer
        iters = self.GetMyDelay(index)/self.GetMyIncrement(index)
        offset = [size/iters for size in pixels] ## multiple by -1 when appropriate
        self._actives[index][1][0] -= offset[0]
        self._actives[index][1][1] -= offset[1]
        space = self._actives[index][1]

        #now either remove the spacer if we have removed enough space, or remove more space if not
        if not smooth or tuple(space) <= (0, 0): ## space > pixels
            #grab the temp sizer
            tempSizerItem = self.Children[self.GetMyPos(index)]
            tempSizer = tempSizerItem.Sizer
            realItemObj = self.GetObject(tempSizer.Children[0])
            #detach the item from it
            tempSizer.Detach(0)
            #add the item back to THIS sizer
            wx.Sizer.Insert(self, self.GetMyPos(index), realItemObj, tempSizerItem.Proportion, tempSizerItem.Flag, tempSizerItem.Border, tempSizerItem.UserData)
            #and remove the temp sizer
            wx.Sizer.Remove(self, tempSizer)
            #remove ourselves from the dictionary, so it doesn't get large
            del self._actives[index]
            #if there is a callback, call it!
            if callback:
                callback()
        else: #still space left, reduce size of spacer
            spacer.SetSpacer(space)
            result = wx.CallLater(self.Increment*1000, self.SmoothHide, item, pixels, smooth, index, spacer, callback, *args, **kwargs)

        #layout each iteration
        self.LayoutProper()

    def SmoothInsert(self, pos, item, *args, **kwargs):
        """
        A smooth insert is basically a smooth show except that the item is
        inserted first.
        """
        smooth = True
        if 'smooth' in kwargs:
            smooth = kwargs['smooth']
            del kwargs['smooth']

        wx.Sizer.Insert(self, pos, item, *args, **kwargs)

        if smooth:
            wx.Sizer.Hide(self, pos)
            self.SmoothShow(pos, *args, **kwargs)

    def SmoothRemove(self, item, *args, **kwargs):
        """
        A smooth remove is basically a smooth hide except that the item is
        deleted in the end.

        Note that the size of the sizer in children won't change until the hide
        is complete.
        """
        self.SmoothHide(item, callback=lambda: wx.Sizer.Remove(self, item), *args, **kwargs)


    Smooth = property(GetSmooth, SetSmooth)
    Delay = property(GetDelay, SetDelay)
    Increment = property(GetIncrement, SetIncrement)


class SmoothBoxSizer(SmoothSizerMixin, wx.BoxSizer):
    """
    An example of using the SmoothSizerMixin to create a SmoothBoxSizer.

    There is no special logic here specific to a BoxSizer. Is there a better
    way to do this, then?
    """
    def __init__(self, orient=wx.HORIZONTAL):
        wx.BoxSizer.__init__(self, orient)
        SmoothSizerMixin.__init__(self)

    def Insert(self, *args, **kwargs):
        return self.SmoothInsert(*args, **kwargs)

    def Hide(self, *args, **kwargs):
        return self.SmoothHide(*args, **kwargs)

    def Remove(self, *args, **kwargs):
        return self.SmoothRemove(*args, **kwargs)


class SmoothStaticBoxSizer(SmoothSizerMixin, wx.StaticBoxSizer):
    """
    A StaticBoxSizer using the SmoothSizerMixin.
    """
    def __init__(self, box, orient=wx.HORIZONTAL):
        wx.StaticBoxSizer.__init__(self, box, orient)
        SmoothSizerMixin.__init__(self)

    def Insert(self, pos, item, *args, **kwargs):
        return self.SmoothInsert(pos, item, *args, **kwargs)

    def Hide(self, item, *args, **kwargs):
        return self.SmoothHide(item, *args, **kwargs)

    def Remove(self, *args, **kwargs):
        return self.SmoothRemove(*args, **kwargs)


class DemoFrame(wx.Frame):
    def __init__(self, parent=None):
        wx.Frame.__init__(self, parent)

        self.panel = panel = wx.Panel(self)

        #you can change the orient and it works
        self.leftSizer = leftSizer = SmoothBoxSizer(wx.VERTICAL)
        leftSizer.Add(wx.Button(panel, label="Hello world!"), smooth=False)
        leftSizer.Add(wx.Button(panel, label="How are you?"), smooth=False)

        self.delayCtrl = wx.lib.intctrl.IntCtrl(panel, value=200, min=0, limited=True, size=(50, -1))
        self.incrementCtrl = wx.lib.intctrl.IntCtrl(panel, value=15, min=0, limited=True, size=(50, -1))
        rightSizer = wx.GridBagSizer(3,5)
        rightSizer.Add(wx.StaticText(panel, label="Delay (milliseconds):"), (0,0))
        rightSizer.Add(wx.StaticText(panel, label="Increment (milliseconds):"), (1,0))
        rightSizer.Add(self.delayCtrl, (0, 1))
        rightSizer.Add(self.incrementCtrl, (1,1))
        rightSizer.Add(wx.Button(panel, label="Prepend a control"), (2,0))
        rightSizer.Add(wx.Button(panel, label="Insert a sizer second"), (3,0))
        rightSizer.Add(wx.Button(panel, label="Hide the second item"), (4,0))
        rightSizer.Add(wx.Button(panel, label="Hide every other item"), (5,0))
        rightSizer.Add(wx.Button(panel, label="Remove the first item"), (6,0))

        sizer = wx.BoxSizer()
        sizer.Add(leftSizer, 1)
        sizer.Add(rightSizer)

        panel.Sizer = sizer
        sizer.Layout()

        self.Bind(wx.EVT_BUTTON, self.onClick)
        self.Show(True)

    def onClick(self, event):
        self.leftSizer.Increment = float(int(self.incrementCtrl.Value)/1000.0)
        self.leftSizer.Delay = float(int(self.delayCtrl.Value)/1000.0)

        label = event.EventObject.Label
        if label == "Prepend a control":
            self.leftSizer.Prepend(wx.Button(self.panel, label="First"))
        elif label == "Hide the second item":
            self.leftSizer.Hide(1)
        elif label == "Insert a sizer second":
            self.Freeze()
            sizer = wx.BoxSizer()
            subsizer = wx.BoxSizer(wx.VERTICAL)
            subsizer.Add(wx.StaticText(self.panel, label="Hello."))
            subsizer.Add(wx.StaticText(self.panel, label="How are you?"))
            sizer.Add(subsizer)
            sizer.Add(wx.TextCtrl(self.panel))
            self.Thaw()
            self.leftSizer.Insert(1, sizer)
        elif label == "Hide every other item":
            for i in range(len(self.leftSizer.GetChildren())):
                if i%2:
                    self.leftSizer.Hide(i)
        elif label == "Remove the first item":
            self.leftSizer.Remove(0)

if __name__ == "__main__":
    app = wx.App(False)
    import wx.lib.intctrl
    frame = DemoFrame()
    app.MainLoop()
