import numpy as np
import os
from tools.globalsettings import lgr as logr
import tools.tools as tls
import csv

def parse_dirname(fname):
    '''
    Read in a directoryname where Imaris encodes a number of conditions, extract them.
    Get the date, infected state, cellid, replicate number, ER marker
    '''
    keys = ['date', 'infected', 'cellid', 'repnr', 'ermarker']
    contents = fname.split('_')
    infecteds = ['Mock','ZIKV']
    markers = ['KDEL', 'Sec61']
    Rep = 'Rep'
    date = None
    infected = None
    cellid = None
    repnr = None
    ermarker = None
    for c in contents:
        if '201' in c and not date:
            if '2018' not in c:
                date = c + '8'
            else:
                date = c
        if infected is None:
            for i in infecteds:
                if i in c:
                    infected = bool(infecteds.index(i))
                    break
        if 'Series' in c and not cellid:
            start = c.index('Series')
            digit = c[start + len('Series'):]
            try:
                cellid = int(digit)
            except ValueError as e:
                logr.error('\t  Failed to decode cellnr {} --> Not an integer for filename \n{}'.format(digit, fname))
                raise e
        if 'Rep' in c and not repnr:
            digit = c.replace('Rep', '')
            try:
                repnr = int(digit)
            except ValueError as e:
                logr.error('\t  Failed to decode Repnr {} --> Not an integer for filename \n{}'.format(digit, fname))
        if not ermarker:
            for marker in markers:
                if marker in c:
                    ermarker = marker
                    break
    if date and '14' in date:  # Edge case
        if repnr == 2:
            repnr = 1
    res = {'date':date, 'infected':infected, 'cellid':cellid, 'repnr':repnr, 'ermarker':ermarker}
    if date and (infected is not None) and cellid and repnr and ermarker:
        return res
    else:
        logr.error('Failed decodion {} \n {}'.format(fname, res))
        raise ValueError('{} failed decoding'.format(fname))

def _check_feature(featurenames, fname):
    '''
    Return feature in featurenames if present in fname
    '''
    for f in featurenames:
        p = fname.find(f)
        if p != -1:
            return f
    return None


def parse_directory(dirname, featurenames=None):
    '''
    Walk a directory, load data from CSVs that have features in featurenames.
    Default = ['Volume', 'Area', 'BoundingBoxAA_Length', 'Sphericity']
    :param dirname: string of an existing path
    :param featurenames: list of strings of features
    :return: dictonary of key --> condition_feature_measure (e.g. Volume_mean, ..)
    '''
    if featurenames is None:
    #'Intensity_Mean_Ch=2_Img=1'
        featurenames = ['Volume', 'Area', 'BoundingBoxAA_Length', 'Sphericity', 'Intensity_Mean_Ch=2_Img=1']
    # logr.info('\tSelected Features: {}'.format(featurenames))
    dirtree = tls.treedir(dirname)
    # logr.info('\t Found {} files'.format(len(dirtree.keys())))
    rx = {}
    for fname, ct in dirtree.items():
        if fname.endswith('.csv'):
            feature = _check_feature(featurenames, fname)
            if feature is None:
                continue
            # logr.debug('\t Reading csv file for feature {}'.format(feature))
            res = None
            try:
                res = parse_featurefile(ct)
            except ValueError as e:
                logr.error('Failed parsing {}'.format(ct))
                raise e
            for k, v in res.items():
                key = '{}_{}'.format(feature, k)
                if key in rx:
                    logr.error('ERROR : {} already in rx'.format(key))
                    raise ValueError
                else:
                    rx['{}_{}'.format(feature, k)] = v
    # logr.info('Decoded a total of {} files'.format(len(rx)))
    return rx


def parse_featurefile(csvfile):
    '''
    Decode a feature file
    :param csvfile: Imaris saves these with 4 leading lines, data on the first column.
    :return: dict of mean, std, sum, min, max, median, N
    '''
    try:
        data = np.loadtxt(csvfile, comments='#', delimiter=',', skiprows=4, usecols=0)
        values = data
        stats = {'mean': np.mean(values), 'std': np.std(values),
                 'sum': np.sum(values), 'min': np.min(values),
                 'max': np.max(values), 'median': np.median(values),
                 'N': len(values)}
        return stats
    except ValueError as e:
        logr.error('Failed decoding csv file \n{} \n Error is {}'.format(csvfile, e))
        raise e

def outwriter(aggregated, outpath, outfile):
    '''
    Write output to a single CSV.
    :param aggegrated: Dict of <columns> -> Values
    :param outpath: existing path
    :param outfile: new csv file
    :return: None
    '''
    columns = []
    for k in aggregated:
        columns = [name for (name, _) in k] + [subk for subk in aggregated[k]]
        break
    # logr.info('\t Columns are {}'.format(columns))
    ct = 0
    with open(os.path.join(outpath, outfile), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(columns)
        for k, v in aggregated.items():
            values = [cv for (_, cv) in k] + [subv for _, subv in aggregated[k].items()]
            writer.writerow(values)
            ct += 1

    logr.info('\t Wrote {} columns and {} rows'.format(len(columns), ct))
