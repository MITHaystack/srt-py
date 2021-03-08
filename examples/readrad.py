"""
readrad.py

"""
from datetime import datetime
import numpy as np
def read(filename):
    """Read in a rad file.py

    Parameters
    ----------
    filename : str
        Input filename.

    Returns
    -------
    outdict : dict
        Holds the info from each entry in the file
    """

    with open(filename) as fp:
        lines = fp.read().splitlines()

    outdict = {}
    for iline in lines:
        # Rad files have 4 types of lines
        linesp = list(filter(None,iline.split(' ')))

        # This has time stamp.
        if linesp[0]=='DATE':
            cur_dict = {linesp[i]:float(linesp[i+1]) if is_number(linesp[i+1]) else linesp[i+1] for i in range(0,len(linesp),2)}
            cur_dict['DATE'] = datetime.strptime(cur_dict['DATE'], '%Y:%j:%H:%M:%S')
        # This has receiver info
        elif linesp[0] =='Fstart':
            linesp.remove('MHz')
            temp_dict = {linesp[i]:float(linesp[i+1]) if is_number(linesp[i+1]) else linesp[i+1] for i in range(0,len(linesp),2)}
            cur_dict.update(temp_dict)
        elif linesp[0] =='Spectrum':
            cur_dict['integrations'] = float(linesp[1])
        elif is_number(linesp[0]):
            cur_dict['spectrum'] = np.array(linesp).astype(float)
            tstp = cur_dict['DATE'].timestamp()
            del cur_dict['DATE']
            outdict[int(tstp)] = cur_dict
    return outdict
def is_number(s):
    """Checks if a string can be translated to a float.

    Parameters
    ----------
    s : string
        Input string.

    Returns
    -------
    boolean
        Answer to such a deep question.
    """
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False
