"""
Format HW assignments that contain a combination of code and
PDFs
"""

import sys
import os
import re
import pipes
import subprocess
import collections
import warnings
import itertools
import shutil
from datetime import datetime

import pyPdf


VERBATIM_TEMPLATE = r"""
\documentclass{article}
\usepackage{geometry}
\usepackage{fancyhdr}

\begin{document}

\setlength{\headheight}{15.2pt}
\pagestyle{fancy}
\fancyhf{}
\lhead{%s: %s}

\begin{verbatim}
%s
\end{verbatim}
\end{document}
"""


LATEX_PROGRAMMING_TEMPLATE = r"""
\documentclass{article}
\usepackage{listings}
\usepackage{color}
\usepackage{textcomp}
\definecolor{listinggray}{gray}{0.9}
\definecolor{lbcolor}{rgb}{0.9,0.9,0.9}
\lstset{
    backgroundcolor=\color{lbcolor},
    tabsize=4,
    rulecolor=,
        basicstyle=\scriptsize,
        upquote=true,
        aboveskip={1.5\baselineskip},
        columns=fixed,
        showstringspaces=false,
        extendedchars=true,
        numbers=left,
        breaklines=true,
        prebreak = \raisebox{0ex}[0ex][0ex]{\ensuremath{\hookleftarrow}},
        frame=single,
        showtabs=false,
        showspaces=false,
        showstringspaces=false,
        identifierstyle=\ttfamily,
        keywordstyle=\color[rgb]{0,0,1},
        commentstyle=\color[rgb]{0.133,0.545,0.133},
        stringstyle=\color[rgb]{0.627,0.126,0.941},
}
\usepackage{geometry}
\usepackage{fancyhdr}

\begin{document}

\setlength{\headheight}{15.2pt}
\pagestyle{fancy}
\fancyhf{}
\lhead{%s: %s}

\begin{lstlisting}[language=%s]
%s
\end{lstlisting}
\end{document}
"""


# dictionary of extensions that this supports and the language of each
EXTENSION_TO_LANGUAGE = {'cc': 'C++', 'c': 'C', 'R': 'R', 'r': 'R',
                         'php': 'PHP', 'rb': 'Ruby', 'cpp': 'C++',
                         'py': 'python', 'pl': 'Perl', 'java': 'Java',
                         'txt': 'verbatim', 'Rnw': 'verbatim',
                         'Rmd': 'verbatim'}


def append_pdf(input, output):
    [output.addPage(input.getPage(page_num))
            for page_num in range(input.numPages)]


class PDFConverter(object):
    """Convert different types of files to be a PDF"""
    def __init__(self, working_directory):
        self.working_directory = working_directory
        if not os.path.exists(working_directory):
            os.mkdir(working_directory)

    def file_in_working_directory(self, infile, new_ext):
        """
        Given an input file, put it in the working directory with a new
        extension
        """
        return os.path.join(self.working_directory,
                                os.path.split(os.path.splitext(infile)[0])[1] +
                                "." + new_ext)

    def convert(self, infile, name):
        """Given an input file, turn it into a PDF"""
        ext = os.path.splitext(infile)[1][1:]
        outfile = self.file_in_working_directory(infile, "pdf")

        if ext.lower() == "pdf":
            # Already in PDF format- no need to do anything but copy
            # also add a marker in case there's a name conflict
            outfile = outfile[:-4] + "__" + outfile[-4:]
            subprocess.Popen(["cp", infile, outfile])
            return outfile

        if ext not in EXTENSION_TO_LANGUAGE:
            warnings.warn("Cannot convert file with extension %s" % ext)
            return None

        language = EXTENSION_TO_LANGUAGE[ext]
        return self.convert_code(infile, name, language)

    def convert_code(self, infile, name, language):
        with open(infile) as inf:
            txt = inf.read()
        infile_n = re.split("\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d",
                                infile)[1][1:].replace("_", "\\_")

        if language == "verbatim":
            # special case
            latex_txt = VERBATIM_TEMPLATE % (name, infile_n, txt)
        else:
            latex_txt = LATEX_PROGRAMMING_TEMPLATE % (name,
                                infile_n, language, txt)
        tempfile = self.file_in_working_directory(infile.replace(" ", "_"), "tex")
        outfile = tempfile[:-4] + ".pdf"
        with open(tempfile, "w") as temp_outf:
            temp_outf.write(latex_txt)

        current_dir = os.getcwd()
        os.chdir(self.working_directory)
        subprocess.Popen(["pdflatex", os.path.split(tempfile)[1]],
                          #stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
                          ).communicate()
        os.chdir(current_dir)

        return outfile


class HWFile(object):
    def __init__(self, f, allowed_names=None):
        # given an input file
        self.file = f
        self.extension = os.path.splitext(f)[1][1:]

        filename = os.path.split(f)[-1]

        self.user = filename.split("_")[1]
        self.date = datetime.strptime(filename.split("_")[3], '%Y-%m-%d-%H-%M-%S')
        self.filename = re.split("\-\d\d\-\d\d\-\d\d\-\d\d\-\d\d_", f)[1]


class HW(object):
    """Represents a single student's homework"""
    def __init__(self, name, infiles, converter):
        """Given the name of a student, a list of files, and a converter"""
        self.name = name

        # get only the most recent of each file
        hw_files = [HWFile(f) for f in infiles]
        hw_files.sort(key=lambda f: f.filename)
        filtered_infiles = [max(g, key=lambda f: f.date).file
                                for k, g in itertools.groupby(hw_files,
                                                    key=lambda f: f.filename)]

        self.infiles = filtered_infiles
        self.converter = converter

    def write(self, pdf_outfolder, file_order=None):
        """Given a folder to write to, and optionally the order of files"""
        outfile = os.path.join(pdf_outfolder, self.name + ".pdf")
        if os.path.exists(outfile):
            # already exists
            return
        # turn each file into a PDF
        PDFs = [self.converter.convert(f, self.name) for f in self.infiles]
        PDFs = filter(None, PDFs)  # filter out those that couldn't convert

        if len(PDFs) == 1:
            # just copy the file over
            # for some reason, shutil.copy creates a corrupt PDF
            os.system("cp %s %s" % (pipes.quote(PDFs[0]), pipes.quote(outfile)))
        else:
            # concatenate
            output = pyPdf.PdfFileWriter()
            for p in PDFs:
                append_pdf(pyPdf.PdfFileReader(file(p, "rb")), output)
            output.write(file(outfile, "wb"))


class HWFolder(object):
    """Represents a folder with HW files in it"""
    def __init__(self, infolder, ignore_exts=None):
        c = PDFConverter("WORKING_DIRECTORY")

        by_student = collections.defaultdict(list)
        for f in os.listdir(infolder):
            # first check if we should ignore this extension
            if ignore_exts and os.path.splitext(f)[1][1:] in ignore_exts:
                continue
            # divide based on Blackboard naming
            by_student[f.split("_")[1]].append(os.path.join(infolder, f))
        self.HWs = [HW(n, lst, c) for n, lst in by_student.items()]

    def write(self, outfolder, file_order=None):
        """Write all HW PDFs to an output folder"""
        if not os.path.exists(outfolder):
            os.mkdir(outfolder)

        for h in self.HWs:
            try:
                h.write(outfolder, file_order)
            except KeyboardInterrupt:
                raise
