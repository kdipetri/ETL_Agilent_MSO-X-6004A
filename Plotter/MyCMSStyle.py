from ROOT import *

def SetAxisTextSizes(obj, extraoffy=0, extraoffx=0):
    obj.GetYaxis().SetTitleOffset(1.1+extraoffy)
    obj.GetYaxis().SetTitleSize(0.0425)
    obj.GetYaxis().SetLabelSize(0.04)
    obj.GetXaxis().SetTitleOffset(1.1+extraoffx)
    obj.GetXaxis().SetTitleSize(0.0425)
    obj.GetXaxis().SetLabelSize(0.04)
#try:
    #obj.GetZaxis().SetTitleOffset(1.1)
    #obj.GetZaxis().SetTitleSize(0.0425)
    #obj.GetZaxis().SetLabelSize(0.04)
#except AttributeError:
#a=1

def SetGeneralStyle():
    gStyle.SetFrameLineWidth(2)

def SetPadStyle(obj):
    obj.SetTicky()
    obj.SetTickx()

def DrawCMSLabels(obj, lumi, simul=0, left_border=0, size=0.045):
    #  obj.Print()
    pad = obj.cd()
    l = pad.GetLeftMargin()
    t = pad.GetTopMargin()
    r = pad.GetRightMargin()
    b = pad.GetBottomMargin()
    lat = TLatex()
    lat.SetTextSize(size)
    lat.SetTextAlign(11)
    lat.SetTextFont(42)
    cmsTag = "#bf{CMS} #it{Preliminary}"
    d1 = lat.DrawLatexNDC(l+0.01+left_border, 1-t+0.015, cmsTag)
    lat.SetTextAlign(31)
    Tag = 'FNAL TB'
    d2 = lat.DrawLatexNDC(1-r-0.001, 1-t+0.015, Tag)
    return [d1,d2]
