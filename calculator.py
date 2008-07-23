import wx
from wx.lib.pubsub import Publisher

class TestPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        leftPanel = wx.Panel(self)
        leftPanel.Sizer = wx.BoxSizer(wx.VERTICAL)

        button = wx.Button(leftPanel, label="Just Fit to my Width")
        button.SetMinSize((250, -1))

        #calcWidget = CollapsableWidget(self, SimpleCalculator, "Calculator")
        calcWidget = SimpleCalculator(leftPanel)

        leftPanel.Sizer.Add(button)
        leftPanel.Sizer.Add(calcWidget)

        # a black panel, so we can see the space better
        rightPanel = wx.Panel(self)
        rightPanel.SetBackgroundColour(wx.BLACK)

        ## MY ATTEMPT
        calcWidget.SetMinSize((button.MinSize[0], -1))
        leftPanel.SetMinSize((button.MinSize[0], -1))

        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(leftPanel, 0, wx.EXPAND)
        self.Sizer.Add(rightPanel, 1, wx.EXPAND)
        self.Layout()


class SimpleCalculator(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.numberClears = True

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.display = wx.TextCtrl(self, -1, '0.00',  style=wx.TE_RIGHT)
        self.display.Bind(wx.EVT_CHAR, self.onChar)
        sizer.Add(self.display, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 4)
        gs = wx.GridSizer(4, 4, 3, 3)

        for lbl in "C ()789/456*123-0.+=":
            if not lbl == ' ':
                btn = wx.Button(self, label=lbl)
                btn.Bind(wx.EVT_BUTTON, self.onButton)
            else:
                btn = wx.StaticText(self)
            gs.Add(btn, 1, wx.EXPAND)

        sizer.Add(gs, 1, wx.EXPAND)
        self.SetSizer(sizer)
        wx.CallLater(50, self.display.SetInsertionPointEnd)

    def onChar(self, event=None, char=None):
        """
        Handles characters, either from a button or a key typed into the text control.

        Supported: 0123456789./*-+
        Special:
            * 'c' or 'C': clears the text ctrl
            * '=' (or WXK_RETURN): evaluates the expression and displays the result
            * WXK_BACK: backspace, deletes the last character

        All other characters/keypresses are discarded.
        """
        if event:
            keycode = event.KeyCode
            if keycode == wx.WXK_BACK:
                self.display.Value = self.display.Value[:-1]
                self.display.SetInsertionPointEnd()
                self.numberClears = False
                return
            elif keycode == wx.WXK_RETURN:
                char = '='
            else:
                char = chr(event.KeyCode)
        else:
            assert char

        if char == '=':
            self.onEnter()
        elif char.upper() == 'C':
            self.display.Value = ""
        elif char in '()0123456789./*-+':
            if char in '()0123456789.' and self.numberClears:
                self.display.Value = ""
            self.numberClears = False
            self.display.AppendText(char)
        else:
            # not a valid character
            return

        self.display.SetFocus()
        self.display.SetInsertionPointEnd()

    def onEnter(self, event=None):
        """
        Attempt to do a simple eval on the text.
        Note no implicit order of operations is respected.
        """
        try:
            # multiple by float first, so 1/2 is 0.50 and not 0.00
            result = eval("1.*"+self.display.Value)
        except:
            return
        self.display.Value = "%.2f"%result
        self.numberClears = True
        self.display.SetInsertionPointEnd()

    def onButton(self, event=None):
        btn = event.EventObject
        command = btn.Label
        self.onChar(char=command)


class CollapsableWidget(wx.Panel):
    def __init__(self, parent, widget, name, *args, **kwargs):
        wx.Panel.__init__(self, parent, -1)
        self.clickLabel = "%s" + " %s"%name

        self.cp = cp = wx.CollapsiblePane(self, label=self.clickLabel%"Hide", style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, cp)

        pane = cp.GetPane()
        self.widget = widget(pane, *args, **kwargs)
        pane.Sizer = wx.BoxSizer()
        pane.Sizer.Add(self.widget, 1, wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(cp, 1, wx.EXPAND)
        #self.OnToggle()

    def OnToggle(self, evt=None):
        self.cp.Collapse(self.cp.IsExpanded())
        self.OnPaneChanged()

    def OnPaneChanged(self, evt=None):
        # redo the layout
        self.Layout()

        # and also change the labels
        if self.cp.IsExpanded():
            modifier = "Hide"
        else:
            modifier = "Show"
        self.cp.Label = self.clickLabel % modifier

        Publisher().sendMessage("CALCULATOR.TOGGLED", modifier.upper())


if __name__ == "__main__":
    app = wx.App(False)
    frame = wx.Frame(None)
    frame.Sizer = wx.BoxSizer()

    ## DEMO OF COLLAPSABLE CALCULATOR
    #frame.Sizer.Add(CollapsableWidget(frame, SimpleCalculator, "Calculator"), 1, wx.EXPAND)

    ## DEMO OF JUST CALCULATOR WIDGET
    #frame.Sizer.Add(SimpleCalculator(frame), 1, wx.EXPAND)

    ## DEMO OF SIZING PROBLEM
    frame.Sizer.Add(TestPanel(frame), 1, wx.EXPAND)
    frame.Size = (800, 600)

    frame.Show(True)
    app.MainLoop()

