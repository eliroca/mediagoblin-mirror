# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PIL import Image
import soundfile
import numpy

SPECTROGRAM_MAX_FREQUENCY = 8000 # Old spectrogram.py sets upper limit to 22050 but
                                 # usually there isn't much detail in higher frequencies
SPECTROGRAM_MIN_FREQUENCY = 20
SPECTROGRAM_DB_RANGE      = 110
# Color palette copied from old spectrogram.py
SPECTROGRAM_COLORS = [(58 / 4, 68 / 4, 65 / 4),
                      (80 / 2, 100 / 2, 153 / 2),
                      (90, 180, 100),
                      (224, 224, 44),
                      (255, 60, 30),
                      (255, 255, 255)]
# The purpose of this table is to give more horizontal
# real estate to shorter sounds files.
# Format: (pixels, (range_min, range_max))
# For sounds with a duration >= _range_min_ and < _range_max_
# give _pixel_ horizontal pixels for each second of audio.
SPECTROGRAM_WIDTH_PERSECOND = [(240, (  0,     20)),
                               (120, ( 20,     30)),
                               ( 60, ( 30,     60)),
                               ( 30, ( 60,    120)),
                               ( 15, (120,    240)),
                               (  6, (240, 100000))] # Upper limit is arbitrary. Sounds with longer
                                                     # duration will still get assigned to the last bucket
SPECTROGRAM_HEIGHT = 500

class AudioBlocksFFT:

    def __init__(self, fileName, blockSize, overlap, minFreq, maxFreq, numBins = None, windowFunction = numpy.hanning):
        self.audioData = soundfile.SoundFile(fileName, 'r')
        self.numChannels = self.audioData.channels
        self.sampleRate = self.audioData.samplerate
        self.minFreq = minFreq
        self.maxFreq = maxFreq
        self.blockSize = blockSize
        self.numBins = numBins
        self.overlap = overlap
        self.windowValues = windowFunction(blockSize)
        self.peakFFTValue = 0
        try:
            # PySoundFile V0.10.0 adds SoundFile.frames property and deprecates __len__()
            self.totalSamples = self.audioData.frames
        except AttributeError:
            self.totalSamples = len(self.audioData)

    def peakFFTAmplitude(self):
        """
        Peak amplitude of FFT for all blocks
        """
        return self.peakFFTValue

    def totalSeconds(self):
        """
        Total length in seconds
        """
        return self.totalSamples / self.sampleRate

    def _filterFreqRange(self, fftAmplitude):
        """
        Given a FFT amplitudes array keep only bins between minFreq, maxFreq
        """
        nyquistFreq = self.sampleRate // 2
        numBins = len(fftAmplitude)
        sliceWidth = nyquistFreq / numBins
        startIdx = int(self.minFreq / sliceWidth)
        endIdx = int(self.maxFreq / sliceWidth)
        if numBins <= endIdx:
            fftAmplitude = numpy.pad(fftAmplitude, (0, 1 + endIdx - numBins), 'constant', constant_values=(0))
        else:
            fftAmplitude = fftAmplitude[:endIdx + 1]
        return fftAmplitude[startIdx:]

    def _resizeAmplitudeArray(self, amplitudeValues, newSize):
        """
        Resize amplitude values array
        """
        if len(amplitudeValues) == newSize:
            return amplitudeValues
        if newSize > len(amplitudeValues):
            # Resize up
            result = numpy.zeros(newSize)
            for idx in range(0, newSize):
                srcIdx = (idx * len(amplitudeValues)) // newSize
                result[idx] = amplitudeValues[srcIdx]
            return result
        # Resize down keeping peaks
        result = numpy.zeros(newSize)
        idx = 0
        for slice in numpy.array_split(amplitudeValues, newSize):
            result[idx] = slice.max()
            idx = idx + 1
        return result

    def __iter__(self):
        """
        Read a block of audio data and compute FFT amplitudes
        """
        self.audioData.seek(0)
        for fileBlock in self.audioData.blocks(blocksize = self.blockSize, overlap = self.overlap):
            # Mix down all channels to mono
            audioBlock = fileBlock[:,0]
            for channel in range(1, self.numChannels):
                audioBlock = numpy.add(audioBlock, fileBlock[:,channel])
            # On the last block it may be necessary to pad with zeros
            if len(audioBlock) < self.blockSize:
                audioBlock = numpy.pad(audioBlock, (0, self.blockSize - len(audioBlock)), 'constant', constant_values=(0))
            # Compute FFT amplitude of this block
            fftAmplitude = self._filterFreqRange(numpy.abs(numpy.fft.rfft(audioBlock * self.windowValues)))
            self.peakFFTValue = max(self.peakFFTValue, fftAmplitude.max())
            # Resize if requested
            if not self.numBins is None:
                fftAmplitude = self._resizeAmplitudeArray(fftAmplitude, self.numBins)
            yield (fftAmplitude, self.audioData.tell() / self.sampleRate)

class SpectrogramColorMap:

    def __init__(self, columnData):
        self.columnData = columnData
        self.width = len(columnData)
        self.height = len(columnData[0])
        self._buildColorPalette()

    def _colorBetween(self, beginColor, endColor, step):
        """
        Interpolate between two colors
        """
        rS, gS, bS = beginColor
        rE, gE, bE = endColor
        r = int(numpy.sqrt((1.0 - step) * (rS * rS) + step * (rE * rE)))
        g = int(numpy.sqrt((1.0 - step) * (gS * gS) + step * (gE * gE)))
        b = int(numpy.sqrt((1.0 - step) * (bS * bS) + step * (bE * bE)))
        r = r if r < 256 else 255
        g = g if g < 256 else 255
        b = b if b < 256 else 255
        return (r, g, b)

    def _buildColorPalette(self):
        """
        Build color palette
        """
        colorPoints = SPECTROGRAM_COLORS
        self.colors = []
        for i in range(1, len(colorPoints)):
            for p in range(0, 200):
                self.colors.append(self._colorBetween(colorPoints[i - 1], colorPoints[i], p / 200))

    def getColorData(self, progressCallback = None):
        """
        Map spectrogram data to pixel colors
        """
        pixels = [self.colors[0]] * (self.width * self.height)
        for x in range(0, self.width):
            for y in range(0, self.height):
                idx = x + self.width * y
                amplitudeVal = self.columnData[x][self.height - y - 1]
                colorIdx = int(len(self.colors) * amplitudeVal)
                colorIdx = colorIdx if colorIdx > 0 else 0
                colorIdx = colorIdx if colorIdx < len(self.colors) else len(self.colors) - 1
                pixels[idx] = self.colors[colorIdx]
            if progressCallback:
                progressCallback(100 * x / self.width)
        return pixels

def drawSpectrogram(audioFileName, imageFileName, fftSize = 1024, fftOverlap = 0, progressCallback = None):
    """
    Draw a spectrogram of the audio file
    """

    # Fraction of total work for each step
    STEP_PERCENTAGE_FFT        = 40
    STEP_PERCENTAGE_NORMALIZE  = 5
    STEP_PERCENTAGE_ACCUMULATE = 10
    STEP_PERCENTAGE_DRAW       = 40
    # Give last 5% to saving the file

    PERCENTAGE_REPORT_STEP = 2

    nextReportedPercentage = PERCENTAGE_REPORT_STEP
    def wrapProgressCallback(percentage):
        nonlocal nextReportedPercentage
        percentage = int(percentage)
        if percentage >= nextReportedPercentage:
            if progressCallback:
                progressCallback(percentage)
            nextReportedPercentage = (1 + percentage // PERCENTAGE_REPORT_STEP) * PERCENTAGE_REPORT_STEP

    def mapColorsProgressCallback(percentage):
        wrapProgressCallback(STEP_PERCENTAGE_FFT + STEP_PERCENTAGE_NORMALIZE + STEP_PERCENTAGE_ACCUMULATE
                             + (STEP_PERCENTAGE_DRAW * (percentage / 100)))

    imageWidthLookup = SPECTROGRAM_WIDTH_PERSECOND
    imageHeight = SPECTROGRAM_HEIGHT

    # Load audio file and compute FFT amplitudes
    fftBlocksSource = AudioBlocksFFT(audioFileName,
                                     fftSize, overlap = fftOverlap,
                                     minFreq = SPECTROGRAM_MIN_FREQUENCY, maxFreq = SPECTROGRAM_MAX_FREQUENCY,
                                     numBins = imageHeight)
    soundLength = fftBlocksSource.totalSeconds()
    fftAmplitudeBlocks = []
    for fftAmplitude, positionSeconds in fftBlocksSource:
        fftAmplitudeBlocks.append(fftAmplitude)
        wrapProgressCallback(STEP_PERCENTAGE_FFT * (positionSeconds / soundLength))

    totalProgress = STEP_PERCENTAGE_FFT

    # Normalize FFT amplitude and convert to log scale
    specRange = SPECTROGRAM_DB_RANGE
    for i in range(0, len(fftAmplitudeBlocks)):
        normalized = numpy.divide(fftAmplitudeBlocks[i], fftBlocksSource.peakFFTAmplitude())
        fftAmplitudeBlocks[i] = ((20*(numpy.log10(normalized + 1e-60))).clip(-specRange, 0.0) + specRange)/specRange
        wrapProgressCallback(totalProgress + STEP_PERCENTAGE_NORMALIZE * (i / len(fftAmplitudeBlocks)))

    totalProgress = totalProgress + STEP_PERCENTAGE_NORMALIZE

    # Compute spectrogram width in pixels
    imageWidthPerSecond, lengthRage = imageWidthLookup[-1]
    for widthPerSecond, lengthLimit in imageWidthLookup:
        limitLow, limitHigh = lengthLimit
        if soundLength > limitLow and soundLength <= limitHigh:
            imageWidthPerSecond = widthPerSecond
            break
    imageWidth = int(imageWidthPerSecond * soundLength)

    # Compute spectrogram values
    columnValues = numpy.zeros(imageHeight)
    spectrogram = []
    x = 0
    for idx in range(0, len(fftAmplitudeBlocks)):
        newX = (idx * imageWidth) // len(fftAmplitudeBlocks)
        if newX != x:
            # Save column
            spectrogram.append(numpy.copy(columnValues))
            x = newX
            columnValues.fill(0)
        columnValues = numpy.maximum(columnValues, fftAmplitudeBlocks[idx])
        wrapProgressCallback(totalProgress + STEP_PERCENTAGE_ACCUMULATE * (idx / len(fftAmplitudeBlocks)))
    spectrogram.append(numpy.copy(columnValues))

    totalProgress = totalProgress + STEP_PERCENTAGE_ACCUMULATE

    # Draw spectrogram
    imageWidth = len(spectrogram)
    colorData = SpectrogramColorMap(spectrogram).getColorData(progressCallback = mapColorsProgressCallback)

    totalProgress = totalProgress + STEP_PERCENTAGE_DRAW

    # Save final image
    image = Image.new('RGB', (imageWidth, imageHeight))
    image.putdata(colorData)
    image.save(imageFileName)

    if progressCallback:
        progressCallback(100)


if __name__ == "__main__":

    import sys

    def printProgress(p):
        sys.stdout.write("\rProgress : {}%".format(p))
        sys.stdout.flush()

    if not (len(sys.argv) == 2 or len(sys.argv) == 3):
        print("Usage:\n{} input_file [output_file]".format(sys.argv[0]))
        exit()

    audioFile = sys.argv[1]

    if 3 == len(sys.argv):
        outputFile = sys.argv[2]
    else:
        outputFile = 'spectrogram.png'

    sys.stdout.write("Input    : {}\nOutput   : {}\n".format(audioFile, outputFile))
    drawSpectrogram(audioFile, outputFile, progressCallback = printProgress)
    sys.stdout.write("\nDone!\n")
