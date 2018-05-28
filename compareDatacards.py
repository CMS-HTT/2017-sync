import sys
import fnmatch

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
from optparse import OptionParser

from varCfg import category_dict
from DisplayManager import DisplayManager

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

colours = [1, 2, 3, 6, 8]
styles = [2, 1, 3, 4, 5]

def getHist(f,cat,histn):
    histogram = f.Get('%(cat)s/%(histn)s'%vars())
    if isinstance(histogram, ROOT.TH1):
        return histogram
    print 'Failed to find a histogram %(cat)s/%(histn)s in file'%vars(), f
    return None

def findDirs(f):
    dirs = []
    for key in f.GetListOfKeys():
        tdir = f.Get(key.GetName())
        if isinstance(tdir, ROOT.TDirectory):
            dirs.append(key.GetName())
    if len(dirs) == 0:
        print 'Failed to find a TDirectory in file', f
    return dirs

def findHists(f, d):
    tdir = f.Get(d)
    hist_names = []
    for key in tdir.GetListOfKeys():
        hist = tdir.Get(key.GetName())
        if isinstance(hist, ROOT.TH1F):
            hist_names.append(key.GetName())
        elif isinstance(hist, ROOT.TH1D):
            hist_names.append(key.GetName())
    if len(hist_names) == 0:
        print 'Failed to find a TH1 in file', f
    return hist_names

def applyHistStyle(h, i):
    h.SetLineColor(colours[i])
    h.SetLineStyle(styles[i])
    h.SetLineWidth(3)
    h.SetFillColor(0)
    h.SetMarkerSize(0)
    h.SetStats(False)


def comparisonPlots(files, titles, category, pname='sync.pdf', ratio=True, contributions=None):

    display = DisplayManager(pname, ratio)
    if contributions is None:
        contributions = ['ZTT','ZLL','VV','W','QCD','TT','data_obs','ggH125','ZJ','ZL']
    
    for template in contributions:
    
        hists = []
        hist_exists = True
        for i, t in enumerate(files):
            if isinstance(getHist(t,category,template),ROOT.TH1):
                hist_exists=True
                h = getHist(t,category,template)
                h.SetTitle(template)
                h.GetXaxis().SetTitle("Visible mass [GeV]")
                applyHistStyle(h,i) 
                hists.append(h)
            else :
                hist_exists =False
                
        if hist_exists == True:
            display.Draw(hists,titles, xmax=500. if not 'ggH' in template and not 'bbH' in template else None)


if __name__ == '__main__':
        
    usage = '''
%prog [options] arg1 arg2 ... argN

    Compares N input datacards - categories to make comparison plots for are specified in varCfg.py/category_dict

'''

    parser = OptionParser(usage=usage)

    parser.add_option('-t', '--titles', type='string', dest='titles', default='Imperial,KIT', help='Comma-separated list of titles for the N input files (e.g. Imperial,KIT)')
    parser.add_option('-r', '--no-ratio', dest='do_ratio', action='store_false', default=True, help='Do not show ratio plots')
    parser.add_option('-f', '--find-categories', dest='find_categories', action='store_true', default=False, help='Determine categories by scanning input files')

    (options,args) = parser.parse_args()

    if len(args) < 2:
        print 'provide at least 2 input root files'
        sys.exit(1)

    titles = options.titles.split(',')
    
    if len(titles) < len(args):
        print 'Provide at least as many titles as input files'
        sys.exit(1)

    for i, arg in enumerate(args):
        if arg.endswith('.txt'):
            f_txt = open(arg)
            for line in f_txt.read().splitlines():
                line.strip()
                if line.startswith('/afs'):
                    args[i] = line
                    break

    tfiles = [ROOT.TFile(arg) for arg in args]
    categories = []

    contributions = {}

    if options.find_categories:
        categories = reduce(set.intersection, [set(findDirs(f)) for f in tfiles])
        for category in categories:
            contributions[category] = reduce(set.intersection, [set(findHists(f, category)) for f in tfiles])

    else:
        if fnmatch.fnmatch(args[0],'*htt_mt.inputs*'):
            categories = category_dict['mt']
        if fnmatch.fnmatch(args[0],'*htt_et.inputs*'):
            categories = category_dict['et']
        if fnmatch.fnmatch(args[0], '*htt_em.inputs*'):
            categories = category_dict['em']
        if fnmatch.fnmatch(args[0], '*htt_tt.inputs*'):
            categories = category_dict['tt']
    

    for category in categories:
        contribution = contributions[category] if category in contributions else None
        comparisonPlots(tfiles, titles, category, '%(category)s-datacard-sync.pdf'%vars(), options.do_ratio, contributions=contribution)

   
