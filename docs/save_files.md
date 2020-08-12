## Small Radio Telescope Docs
#### Save File Details

The SRT Currently supports saving data into 3 different file types:
 - [Digital RF](https://github.com/MITHaystack/digital_rf) - Saves raw I/Q samples
 - [FITS](https://docs.astropy.org/en/stable/io/fits/) - Saves calibrated spectra
 - [rad](https://www.haystack.mit.edu/haystack-public-outreach/srt-the-small-radio-telescope-for-education/) - Saves calibrated spectra (see pswriter documentation for more info)

Each format has different techniques for encoding metadata about the status of the SRT when it was taking the data, and so each has nearly the same data but accessible in a different manner.  Examples for reading the main data and metadata for each file format follow

##### Digital RF - GNU Radio

Since digital_rf is compatible with GNU Radio, it is possible to load a stream of raw samples directly into a GNU Radio Companion flowgraph once the gr_digital_rf library is installed.  This process simply uses the 'Digital RF Channel Source' block with its channel set to the path to the folder containing the data.  In addition, any metadata will appear in the stream as tags associated with the sample(s) that they were saved with.

Form more information about using [GNU Radio Companion](https://wiki.gnuradio.org/index.php/Guided_Tutorial_GRC) or handling GNU Radio [tagged streams](https://wiki.gnuradio.org/index.php/Stream_Tags), see the GNU Radio docs.

##### Digital RF - Manual Usage

Multiple detailed examples for reading Digital RF files can be found in the examples/ directory of the [digital_rf repository](https://github.com/MITHaystack/digital_rf/blob/master/python/examples/).

##### FITS

The SRT software uses AstroPy for saving spectrum data, and so reading the data back can be performed easily with AstroPy as well.  Notably, each spectra generated is saved into its own HDU, which in addition to the typical FITS metadata, each spectra has all of its SRT metadata saved in a JSON-encoded string in the header "METADATA".

```Python
from astropy.io import fits
import json
hdul = fits.open(fits_filename)
for hdu in hdul:
    metadata = json.loads(hdu.header["METADATA"])
    data = hdu.data
    print(metadata)
    print(data)
```

##### rad

The below excerpt is a modification (namely, to have larger buffers and excluding doing anything with the loaded data for simplicity) on the original pswriter.c code which parses .rad files and generates .ps graphs from their content.  More information of [PS Writer](https://www.haystack.mit.edu/wp-content/uploads/2020/07/srt_Pswriter_instructions.pdf) can be found on the Haystack Observatory [website](https://www.haystack.mit.edu/haystack-public-outreach/srt-the-small-radio-telescope-for-education/).

```c
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <string.h>
#include <sched.h>

int main(void)
{
  char txt[80], fnam[80], datafile[80];
  int i, j, jmax, k, np, j1, j2, n3, npoint, yr, da, hr, mn, sc, obsn1, obsn2;
  double xx, yy, dmax, ddmax, dmin, slope, dd, ddd, totpp, scale, sigma, freq, freqq, fstart, fstop, vstart, vstop, xoffset;
  double freqsep, x1, x2, y1, y2, wid, sx, sy, yoffset, x, y, xp, yp, av, avx, avy, avxx, avxy, psx1, psx2, psy1, psy2, yps;
  double restfreq;

  //Added variables for data input from file
  double aznow, elnow, tsys, tant, vlsr, glat, glon, bw, fbw, integ;
  int nfreq, nsam, bsw, intp;
  char soutrack[80*100], buf[80*100];
  double pp[512*64*2];
  FILE *file1 = NULL;
  FILE *dfile=NULL;

  //Ask user to enter name of data file to be read
  printf("Enter name of data file: ");
  scanf("%s", datafile);
  if ((dfile = fopen(datafile, "r")) == NULL) {
    printf("cannot read %s\n", datafile);
    return 0;
  }

  //Ask user to enter observation to be read
  printf("Enter observation number to read: ");
  scanf("%d", &obsn1);

  obsn2=-1; //Initialize obsn2 for first comparison
  while(obsn1!=obsn2)	//Scan in data file until entered and scanned observation numbers match
  {
    //Scan in first two lines of data
    fscanf(dfile, "%[^\n]\n", buf);
    if (buf[0] == '*')
    {
        fscanf(dfile, "DATE %4d:%03d:%02d:%02d:%02d obsn %3d az %lf el %lf freq_MHz %lf Tsys %lf Tant %lf vlsr %lf glat %lf glon %lf source %s\n",
				&yr, &da, &hr, &mn, &sc, &obsn2, &aznow, &elnow, &freq, &tsys, &tant, &vlsr, &glat, &glon, soutrack);
    }
    else
    {
        sscanf(buf, "DATE %4d:%03d:%02d:%02d:%02d obsn %3d az %lf el %lf freq_MHz %lf Tsys %lf Tant %lf vlsr %lf glat %lf glon %lf source %s\n",
        	      	         &yr, &da, &hr, &mn, &sc, &obsn2, &aznow, &elnow, &freq, &tsys, &tant, &vlsr, &glat, &glon, soutrack);
		}
		fscanf(dfile, "Fstart %lf fstop %lf spacing %lf bw %lf fbw %lf MHz nfreq %d nsam %d npoint %d integ %lf sigma %lf bsw %d\n",
      	                 &fstart, &fstop, &freqsep, &bw, &fbw, &nfreq, &nsam, &npoint, &integ, &sigma, &bsw);
    //Calculate a few things that are based on early data in the file and are needed to define later scanning from the file
    np = npoint;
    j1 = np * 0;
    j2 = np * 1;
    //Scan in spectrum data
    fscanf(dfile, "Spectrum %2d integration periods\n", &intp);
    for (j=0; j<j2; j++)
      fscanf(dfile, "%lf ", &pp[j]);
    fscanf(dfile, "\n");
    if (fabs(pp[0] - pp[1]) > 200)
    {
      intp = 1;
      fseek(dfile, -9 * np, SEEK_CUR);
      fscanf(dfile, "Spectrum \n");
      for (j=0; j<j2; j++)
        fscanf(dfile, "%lf ", &pp[j]);
      fscanf(dfile, "\n");
    }
  }

  //Print out scanned data
  printf("Data scanned from file:\n");
  printf("DATE %4d:%03d:%02d:%02d:%02d obsn %3d az %3.0f el %2.0f freq_MHz %10.4f Tsys %6.3f Tant %6.3f vlsr %7.2f glat %6.3f glon %6.3f source %s\n",
                        yr, da, hr, mn, sc, obsn2, aznow, elnow, freq, tsys, tant, vlsr, glat, glon, soutrack);
  printf("Fstart %8.3f fstop %8.3f spacing %8.6f bw %8.3f fbw %8.3f MHz nfreq %d nsam %d npoint %d integ %5.0f sigma %8.3f bsw %d\n",
                        fstart, fstop, freqsep, bw, fbw, nfreq, nsam, npoint, integ, sigma, bsw);
  printf("Spectrum     %d integration periods\n", intp);
  for (j=0; j<j2; j++)
    printf("%8.3f ", pp[j]);
  printf("j=%d\n", j);
}
```
