"""
Format HW assignments that contain a combination of code and
PDFs
"""

import sys
import os
import re
import subprocess
import collections

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
EXTENSION_TO_LANGUAGE = {'cc': 'C++', 'c': 'C', 'R': 'R', 'php': 'PHP',
                         'rb': 'Ruby', 'cpp': 'C++', 'py': 'python',
                         'pl': 'Perl', 'java': 'Java', 'txt': 'verbatim'}


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
            subprocess.Popen(["cp", infile, outfile])
            return outfile

        print infile
        if ext not in EXTENSION_TO_LANGUAGE:
            raise Exception("Cannot convert file with extension %s" % ext)

        language = EXTENSION_TO_LANGUAGE[ext]
        self.convert_code(infile, outfile, name, language)
        return outfile

    def convert_code(self, infile, outfile, name, language):
        with open(infile) as inf:
            txt = inf.read()
        print infile
        infile_n = re.split("\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d",
                                infile)[1][1:].replace("_", "\\_")

        if language == "verbatim":
            # special case
            latex_txt = VERBATIM_TEMPLATE % (name, infile_n, txt)
        else:
            latex_txt = LATEX_PROGRAMMING_TEMPLATE % (name,
                                infile_n, language, txt)
        tempfile = self.file_in_working_directory(infile, "tex")
        with open(tempfile, "w") as temp_outf:
            temp_outf.write(latex_txt)

        current_dir = os.getcwd()
        os.chdir(self.working_directory)
        subprocess.Popen(["pdflatex", os.path.split(tempfile)[1]],
                          #stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
                          ).communicate()
        os.chdir(current_dir)

        return outfile


class HW(object):
    """Represents a single student's homework"""
    def __init__(self, name, infiles, converter):
        """Given the name of a student, a list of files, and a converter"""
        self.name = name
        self.infiles = infiles
        self.converter = converter

    def write(self, pdf_outfolder, file_order=None):
        """Given a folder to write to, and optionally the order of files"""
        outfile = os.path.join(pdf_outfolder, self.name + ".pdf")
        # turn each file into a PDF
        PDFs = [self.converter.convert(f, self.name) for f in self.infiles]
        # concatenate
        output = pyPdf.PdfFileWriter()
        for p in PDFs:
            append_pdf(pyPdf.PdfFileReader(file(p,"rb")), output)
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
            h.write(outfolder, file_order)

if __name__ == "__main__":
    [infolder, outfolder] = sys.argv[1:]
    f = HWFolder(infolder, ["txt", "fasta"])
    f.write(outfolder)
