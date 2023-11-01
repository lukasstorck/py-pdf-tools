import argparse
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import pathlib
import PyPDF2
import scipy.cluster
import subprocess
from bs4 import BeautifulSoup
from pdf2image import convert_from_path
from tqdm.contrib.concurrent import process_map


def drawColorFrequency(colors, frequency):
    total = frequency.sum()
    for i in range(len(frequency)):
        plt.scatter(i, frequency[i], color=colors[i]/255, edgecolors='b', s=1000, marker='s')
        plt.text(i, frequency[i], s=str(round(frequency[i]/total * 100, 1)) + '%', ha='center', va='center', color=(1 - colors[i]/255))
    plt.tight_layout()
    plt.yscale('log')
    plt.show()

def getMostFrequentColor(image, maxColors=8):
    data = np.array(image)
    # reformat data to list of pixels, shape: (#pixel, 1) or (#pixel, 3)
    if len(data.shape) == 2:
        pixels = data.reshape(np.product(data.shape[:2]), 1).astype(float)
    elif len(data.shape) == 3:
        pixels = data.reshape(np.product(data.shape[:2]), data.shape[2]).astype(float)

    # choose <maxColors> colors that represent the image best
    codebook, _ = scipy.cluster.vq.kmeans2(pixels, maxColors, minit='++')
    codebook = codebook.round()
    # group each pixel to a color
    code, _ = scipy.cluster.vq.vq(pixels, codebook)
    # count the assignments (to colors)
    frequency, _ = np.histogram(code, len(codebook))

    # only for testing
    # drawColorFrequency(codebook, frequency)

    # get the most frequent color
    iMax = np.argmax(frequency)
    color = codebook[iMax]
    return color

def readableSlideshowImg(filename, resolution=80, firstPage=None, lastPage=None, maxColorDetection=8, overwriteBackgroundColor=None, queue=None):
    # load pages
    pages = convert_from_path(filename, resolution, first_page=firstPage, last_page=lastPage, grayscale=False)

    neededSlides = list()

    for i in range(len(pages) - 1):
        curr = np.array(pages[i])
        next = np.array(pages[i+1])

        # most frequent color is probably background color
        bgColor = overwriteBackgroundColor
        if overwriteBackgroundColor is None:
            bgColor = getMostFrequentColor(curr, maxColors=maxColorDetection)

        # compare the current slide to the next and fill the pixel that are different with the background color
        # in case that there was only information added (e.g. a new sentence) these pixels revert to the first image ("curr")
        # and the image "diff" should be the same as the image "curr"
        diff = np.where(curr == next, curr, np.full_like(curr, bgColor))
        
        # a slide is not needed if it contains a subset of information in regards to the next slide (slideshow revealing one aspect at a time)
        if (curr != diff).any():
            neededSlides.append(i)

    neededSlides.append(len(pages) - 1)
    if queue is not None:
        queue.put(neededSlides)
    return neededSlides # first page of original pdf is 0 not 1


def readableSlideshowHtml(filename, firstPage=None, lastPage=None, queue=None):
    # create pdf2htmlex commandline parameters
    parameters = ['pdf2htmlEX', '--dpi', '0', '--dest-dir', filename.parent]
    if firstPage is not None:
        parameters += ['-f', str(firstPage)]
    if lastPage is not None:
        parameters += ['-l', str(lastPage)]
    parameters += [filename]
    # generate html
    subprocess.run(parameters, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    # load html
    html = None
    with open(filename.with_suffix('.html')) as f:
        html = BeautifulSoup(f, 'html.parser')
    pages = list(html.select('#page-container > div'))
    
    neededSlides = list()
    # determine whether a slide is needed or not
    for i in range(len(pages) - 1):
        curr = pages[i]
        next = pages[i+1]

        # pdf2htmlEX mostly generates the same elements for similar slides,
        # but then hides the elements that are not shown yet
        # probably due to underlying structure in the pdf
        if curr.text != next.text:
            neededSlides.append(i)
    neededSlides.append(len(pages) - 1)

    filename.with_suffix('.html').unlink()  # delete .html file
    if queue is not None:
        queue.put(neededSlides)
    return neededSlides # first page of original pdf is 0 not 1


def saveRelevantPages(file, relevantPages, outputPrefix='readable_'):

    pdf = PyPDF2.PdfFileReader(str(file))
    pdfWriter = PyPDF2.PdfFileWriter()

    # add relevant pages
    for page in relevantPages:
        pdfWriter.addPage(pdf.getPage(page))
    
    # save with new name
    with open(file.parent / (outputPrefix + file.name), 'wb') as f:
        pdfWriter.write(f)


def parse(fixedString=None):
    parser = argparse.ArgumentParser(
        usage='usage: readableSlideshow.py [options] FILE [FILE ...]',
        description='Read in PDF files and return a copy with any page removed, that only has content, which is also shown on the subsequent page. Can be used to turn slideshows, made for presenting, into a script-like set of slides.',
        epilog='You can process multiple files by including all filenames or using the parent directory to process all PDF files in that directory. You can also give multiple directories. Heck, you even can mix files and folders. The resolution ("-r") in which the PDF pages are read in, has a huge impact on the runtime.'
        )
    
    parser.add_argument('file', metavar='FILE', type=str, nargs='+', help='a pdf file or folder to process')
    parser.add_argument('-r', '--resolution', '--dpi', metavar='DPI', type=int, help='resolution in dpi while scanning the pdf (default: 80)', default=80)
    parser.add_argument('-o', '--output', metavar='OUT', type=str, help='a prefix for the output filename (default: "readable_")', default='readable_')
    parser.add_argument('--first', metavar='NUM', type=int, help='first page to read in (default: 1)')
    parser.add_argument('--last', metavar='NUM', type=int, help='last page to read in (default: MAX)')
    parser.add_argument('-m', '--mode', type=str, help='mode for relevant pages detection (IMG, HTML or BOTH, default: BOTH)', default='BOTH')
    parser.add_argument('--maxColors', metavar='NUM', type=int, help='amount of colors used in clustering to find the background color, for mode IMG (default: 8)', default=8)
    parser.add_argument('-obgc', '--overwriteBackgroundColor', metavar='COLORHEX', type=str, help='use this color as background color and skip background color calculation, for mode IMG (like "-obgc #ffffff")')

    if fixedString:
        return parser.parse_args(fixedString.split())
    else:
        return parser.parse_args()

def checkArguments(args):
    for string in args.file:
        path = pathlib.Path(string)
        if path.is_file():
            # correct file ending?
            if path.suffix != '.pdf':
                raise ValueError(f'"{path.resolve()}" is not a ".pdf" file.')
        elif path.is_dir():
            # are there any pdf files?
            noPdfFiles = True
            for child in path.iterdir():
                if child.is_file() and child.suffix == '.pdf':
                    noPdfFiles = False
                    break
            if noPdfFiles:
                print(f'* INFO "{path.resolve()}" contains no ".pdf" file.')

        else:
            raise ValueError(f'"{path.resolve()}" is neither an existing file nor folder.')

    # do not know if this can even happen (how to enter an empty string?)
    # if args.output == '':
    #     print('* WARNING: An empty string overwrites the currently existing file.')
    #     input('Continue? (Enter)')

    if args.first is not None and args.last is not None and args.first >= args.last:
        raise ValueError(f'The page numbers do not fit together: first ({args.first}) must be smaller than last ({args.last})')

    if args.overwriteBackgroundColor and args.maxColors != 8:
        print('* INFO: "--maxColors MAXCOLORS" is ignored due to "--overwriteBackgroundColor COLORHEX" being set')
    
    if args.mode not in ['IMG', 'HTML', 'BOTH']:
        raise Exception('Either leave out the mode argument or specify any of these modes: IMG or HTML')


def runJobs(jobDesc):
    args, file = jobDesc

    argsImg = {'filename' : file,
              'resolution' : args.resolution,
              'firstPage' : args.first,
              'lastPage' : args.last,
              'maxColorDetection' : args.maxColors,
              'overwriteBackgroundColor' : args.overwriteBackgroundColor,
              'queue' : multiprocessing.Queue() if args.mode == 'BOTH' else None}
    argsHtml = {'filename' : file,
                'firstPage' : args.first,
                'lastPage' : args.last,
                'queue' : multiprocessing.Queue() if args.mode == 'BOTH' else None}
    if args.mode == 'IMG':
        relevantPages = readableSlideshowImg(**argsImg)
    if args.mode == 'HTML':
        relevantPages = readableSlideshowHtml(**argsHtml)
    if args.mode == 'BOTH':
        pImg = multiprocessing.Process(target=readableSlideshowImg, kwargs=argsImg)
        pImg.start()
        pHtml = multiprocessing.Process(target=readableSlideshowHtml, kwargs=argsHtml)
        pHtml.start()

        pImg.join()
        pHtml.join()

        img = argsImg['queue'].get()
        html = argsHtml['queue'].get()
        relevantPages = list(set(img).intersection(html))
        relevantPages.sort()
    else:
        raise Exception('Someone fucked up names of variables again')
    saveRelevantPages(file, relevantPages, outputPrefix=args.output)



if __name__ == '__main__':
    # parse commandline arguments
    args = parse()
    # argument checks
    checkArguments(args)

    # iterate over list of files and folders, extract all pdf files
    # exclude files that begin with the output prefix
    files = list()
    for string in args.file:
        path = pathlib.Path(string)
        if path.is_file() and args.output not in path.name:
            files.append(path)
        if path.is_dir():
            for child in path.iterdir():
                if child.is_file() and args.output not in child.name and child.suffix == '.pdf':
                    files.append(child)
    
    # iterate over gathered files and make 'em readable
    jobs = [(args, file) for file in files]
    process_map(runJobs, jobs)
