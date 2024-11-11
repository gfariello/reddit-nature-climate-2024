# Reddit Nature CommsEnv Climate 2024

This repository contains the code, instructions, and data necessary to reproduce
the findings in our paper, tentatively accepted to *Nature Communications Earth
& Environment*. The study conducts a comprehensive, large-scale analysis of
discussions surrounding climate change and related topics on Reddit. Our
data-driven approach explores sentiment, terminology trends, and language
complexity across millions of Reddit posts over a 16-year period.

## Table of Contents

- [Quick Start](#quick-start) for the impatient.
  - [Obtaining Relevant Data](#obtaining-relevant-data)
  - [Generating Figures](#generating-figures)
- [Project Overview](#project-overview)
- [Data Description](#data-description)
- [Methodology](#methodology)
- [Reproducibility](#reproducibility)
- [Preprocessing Original Reddit Data (Optional)](#preprocessing-original-reddit-data-optional)
  - [Setup and Installation](#setup-and-installation)
  - [Step 00: Obtaining Complete Reddit Data](#step-00-obtaining-complete-reddit-data)
    - [Prerequisites](#prerequisites)
    - [Step 00 Substep 01: Navigate to AcademicTorrents.com](#step-00-substep-01-navigate-to-academictorrentscom)
    - [Step 00 Substep 02: Find the Reddit Dataset](#step-00-substep-02-find-the-reddit-dataset)
    - [Step 00 Substep 03: Download the .torrent File or Use the Magnet Link](#step-00-substep-03-download-the-torrent-file-or-use-the-magnet-link)
    - [Step 00 Substep 04: Start the Download with aria2c](#step-00-substep-04-start-the-download-with-aria2c)
    - [Step 00 Substep 05: Verify and Access the Data](#step-00-substep-05-verify-and-access-the-data)
    - [Tips and Notes](#tips-and-notes)
  - [Step 01 Extracting Climate Related Posts](#step-01-extracting-climate-related-posts)
  - [Step 02 Converting JSONL Files to CSV Files](#step-02-converting-jsonl-files-to-csv-files)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

If what you want to do is replicate the findings without doing the very lengthy
 pre-processing of the original ~10TB of Reddit data, you can use use the few
 gigabytes of data available below and you can use the *live* [Google Colab
 Notebook](https//colab.research.google.com/drive/1PpIRVvIvzowMVH44hjXSuFX6AGdV93YI?authuser=1#revisionId=0B1uzaQumGqFNRm5BdU94a0YydFk0Ym5jZFEwMjEvSUZsbkNzPQ)
 to run the analyses. It will download the data for you.

### Obtaining Relevant Data

All the data used in the manuscript is freely available at [Data Repository on
FigShare](http://dx.doi.org/10.6084/m9.figshare.26828467). This section, along
with the following [Generating Figures](#generating-figures) section, is
sufficient to replicate the findings and figures of the study. If you are only
interested in reproducing the figures and analysis, you can skip the
[Preprocessing Original Reddit Data (Optional)](#preprocessing-original-reddit-data-optional)
and subsequent sections.

### Generating Figures

All figures presented in the analysis can be reproduced using the extracted and
derived data by accessing the live Google Colab page. This Colab notebook
provides an interactive environment where users can run the analyses and
generate each figure step-by-step.

To get started, open the Colab notebook using the following link:

[Google Colab: Climate Data Analysis and
Visualization](https://colab.research.google.com/drive/1PpIRVvIvzowMVH44hjXSuFX6AGdV93YI?authuser=1#revisionId=0B1uzaQumGqFNRm5BdU94a0YydFk0Ym5jZFEwMjEvSUZsbkNzPQ)

Simply run the notebook to load the data, execute the analyses, and produce the
visualizations. This approach ensures full reproducibility of the figures from
the extracted Reddit data.

## Project Overview

This repository has only been tested on Ubuntu 20.04 LTS and 22.04 LTS.

This repository enables the analysis and replication of our findings on the
linguistic and sentiment dynamics of "climate change" vs. "global warming" in
Reddit discourse. Leveraging Reddit’s extensive archives, we analyzed over 11.5
billion posts and comments, identifying trends that reveal shifting public
engagement and sentiment. Key insights include:

- A notable shift from "global warming" to "climate change" as the dominant term
  in Reddit discussions post-2013.

- Sentiment differences where "global warming" is often associated with more
  positive sentiment than "climate change."

- Increasing linguistic complexity in discussions involving "climate change,"
  potentially impacting accessibility and engagement.

### Processing Large and Compressed Data

This project uses `PolyReader` and `PolyWriter` for efficient reading and
writing of Reddit JSONL files, even if they are compressed or located remotely.
These utilities support a variety of compression formats (`.zst`, `.bz2`,
`.gzip`) and access methods, including:

- **Local Storage**: Read and write from files stored locally on disk.
- **Remote Access**: Supports FTP, SFTP, SSH, HTTPS, and other protocols,
    enabling direct processing without needing to download the entire dataset to
    local storage.
- **On-the-Fly Decompression**: Automatically decompresses data while reading,
    saving storage space and processing time for large datasets.

With `PolyReader` and `PolyWriter`, there’s no need to decompress files in
advance, even for remote or compressed data sources, making it easier to process
Reddit’s vast data archives.

## Data Description

Our analysis leverages data from:

- **Pushshift.io**: A comprehensive Reddit dataset, including posts and comments
    from 2005 through 2021.

- **Google Trends**: Historical search trends for "climate change" and "global
    warming," providing a secondary perspective on public interest.

Pre-processed and supplementary data are available on FigShare for extended analysis:

- **[Data Repository on FigShare](http://dx.doi.org/10.6084/m9.figshare.26828467)**: Includes all
    raw data, cleaned data files, and analysis results.

## Methodology

Our analysis includes:

- **Sentiment Analysis**: VADER and TextBlob were used to gauge sentiment,
    polarity, and subjectivity.

- **Language Complexity**: Readability metrics assess the complexity of climate
    discussions across subreddits.

- **N-gram Analysis**: Unigram, bigram, and trigram analyses identify popular
    phrases and terminology trends.

- **Temporal Analysis**: Examines trends over time to uncover shifts in
    terminology, engagement, and sentiment.

Details on filtering techniques and regular expressions are provided in the supplementary materials.

## Reproducibility

To support reproducibility, the repository includes all code, configurations,
and data used in the study. Detailed instructions are provided to replicate each
step in the analysis, from data collection to sentiment scoring and
visualization.

## Preprocessing Original Reddit Data (Optional)

**Note 1**: As mentioned in the [Quick Start](#quick-start) guide, the
  pre-processed and rerived data is available with a live notebook for analysis
  which can reproduce all the findings.

**Note 2**: At the time of this writing, we recommend that you have approximately
  5 to 6 terabytes of free space and either access to a very large SMP system or
  an HPC cluster.

### Setup and Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:gfariello/reddit-nature-commsenv-climate-2024.git
   cd reddit-nature-commsenv-climate-2024
   ```

2. **Install dependencies**
   Ensure Python 3.8+ is installed. Then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Reddit API credentials**
   To collect Reddit data, configure a `.env` file with your Reddit API
   credentials:

   ```plaintext
   CLIENT_ID=<your-client-id>
   CLIENT_SECRET=<your-client-secret>
   USER_AGENT=<your-user-agent>
   ```

### Step 00: Obtaining Complete Reddit Data

**NOTE:** This is optional. The raw extracted data is provided via the
[Data Repository on FigShare](http://dx.doi.org/10.6084/m9.figshare.26828467).

This guide provides detailed steps to download Reddit data in JSONL format from
AcademicTorrents.com using a non-GUI torrent tool.

#### Prerequisites

1. **Install a Torrent Client**: Academic Torrents uses the BitTorrent protocol
   to distribute files. If you’re using Linux and prefer a non-GUI tool, you can
   use **aria2c**:

  - **aria2c** (Linux, macOS): Install via package manager
     ```bash
     # For Debian/Ubuntu
     sudo apt-get install aria2

     # For Fedora/RHEL
     sudo dnf install aria2
     ```

2. **Ensure Sufficient Storage**: The Reddit dataset can be very large (over 2.8
   TB), so make sure you have ample storage space.

#### Step 00 Substep 01: Navigate to AcademicTorrents.com

1. Open a web browser and go to
   [AcademicTorrents.com](https://academictorrents.com).

2. In the search bar, type "Reddit" and press Enter. This will list available
   Reddit datasets, including monthly exports and the full dataset.

#### Step 00 Substep 02: Find the Reddit Dataset

1. Look for the dataset titled something similar to **Reddit Data JSONL** or
   **Complete Reddit Dataset**. This dataset typically contains Reddit posts and
   comments in JSONL format, organized by year or month.

2. Click on the dataset name to view details, including the dataset description,
   size, and download options.

#### Step 00 Substep 03: Download the .torrent File or Use the Magnet Link

1. On the dataset page, you’ll see options to either **Download .torrent** or
   **Copy Magnet Link**.
   - If using the **Download .torrent** option, save the `.torrent` file to your
     computer.
   - If using the **Magnet Link**, copy it to your clipboard (right-click and
     select “Copy link address”).

#### Step 00 Substep 04: Start the Download with aria2c

1. Open a terminal on your Linux machine.
2. Use one of the following commands depending on whether you downloaded a
   `.torrent` file or copied the magnet link.

   - **If using a `.torrent` file**:
     ```bash
     aria2c /path/to/yourfile.torrent -d /path/to/save/location
     ```
   - **If using a magnet link**:
     ```bash
     aria2c 'magnet:?xt=urn:btih:<your-magnet-link>' -d /path/to/save/location
     ```
3. **Monitor the Download**: aria2c will display the progress of each downloaded
   file in the terminal. The download time will vary depending on your internet
   speed and the dataset size.

#### Step 00 Substep 05: Verify and Access the Data

1. After the download is complete, navigate to the folder where you saved the
   dataset.

2. The files should be in **JSONL** format, where each line in a file is a JSON
   object representing a Reddit post or comment. These files may be compressed
   in `.zst` (Zstandard) format, typically named as `RC_YYYY-MM.zst` for
   comments and `RS_YYYY-MM.zst` for submissions. Decompression is necessary
   before processing, or you can use tools that support on-the-fly
   decompression.

#### Tips and Notes

The following files are provided to check consistency. We updated them to include
the most recent files available at the time of this writing:
```plaintext
        Checksums/step-00-file-md5sums.txt
        Checksums/step-00-file-record-counts.csv
```

- **Monitor Disk Space**: Reddit datasets are large, and you may need to free up
    space as needed.

- **Check File Integrity**: aria2c will automatically verify the integrity of
    downloaded files.

- **JSONL Format**: JSONL (JSON Lines) format is efficient for large datasets
    but requires line-by-line processing, as shown in the example code above.

Following these steps will allow you to download and work with Reddit data from
AcademicTorrents.com efficiently.

### Step 01: Extracting Climate Related Posts

From within the repository directory, run the following command:

```bash
bash step-01.sh  --input-dir INPUT_DIR --output-dir OUTPUT_DIR --threads NUM_THREADS
```

Be sure to chage `INPUT_DIR` to the parent directory in which (they can be
several layers deep) the downloaded `RC_20*.zst` or `RS_20*.zst` files are
located. If you downloaded the torrents described above, this will be the
directory in which the `reddit` directory sits. Be to set `OUTPUT_DIR` to where
you want the new files to be saved. This should not be the same as
`INPUT_DIR`. Set `NUM_THREADS` to the maximum number of threads to run
simultaneously. Each process consumed about 2.2GB of RAM on our systems, so keep
that in mind. By default, it will use all the processors available.

If you set up the command-line correctly, this will find all files matching the
`RC_20*.zst` or `RS_20*.zst` filenames in `INPUT_DIR` and extract all the posts
whose title or body match the following regular expression:

`climat.*chang|chang.*climat|glob.*warm|warm.*glob`

And save them, in zstandard compressed format into `OUTPUT_DIR` with the same
filename. *CAUTION*: Again, please make sure that `INPUT_DIR` and `OUTPUT_DIR`
are not the same.

When this is complete, move on to the next step.

### Step 02: Converting JSONL Files to CSV Files

From within the repository directory, run the following command:

```bash
bash step-02.sh  --input-dir INPUT_DIR --threads NUM_THREADS
```

**Note**: In this case `INPUT_DIR` will likely be the `OUTPUT_DIR` from *Step 01*.

The processes spawned by this script tend to use less RAM since they are running
on much smaller files; however, use caution when running many, nevertheless.

Running the above will create CSV files ready for processing for subsequent steps.

## Contributing

We welcome contributions! Please fork the repository and create a pull request
with your proposed changes. Ensure code style consistency and include tests
where relevant.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file
for more details.

---

This repository provides a comprehensive foundation for replicating and
extending our analysis of climate change discourse on Reddit. We hope it serves
as a valuable resource for researchers and advocates seeking insights into
public perceptions of climate issues.
