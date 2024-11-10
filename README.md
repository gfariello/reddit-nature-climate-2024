# Reddit Nature COMMSENV Climate 2024

This repository contains the code, instructions, and data necessary to reproduce
the findings in our paper, tentatively accepted to *Nature Communications Earth
& Environment*. The study conducts a comprehensive, large-scale analysis of
discussions surrounding climate change and related topics on Reddit. Our
data-driven approach explores sentiment, terminology trends, and language
complexity across millions of Reddit posts over a 16-year period.

## Table of Contents

- [Project Overview](#project-overview)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Data](#data)
- [Methodology](#methodology)
- [Reproducibility](#reproducibility)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

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

# Downloading Reddit Data from AcademicTorrents.com

This guide provides detailed steps to download Reddit data in JSONL format from AcademicTorrents.com using a non-GUI torrent tool.

## Prerequisites

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

## Step-by-Step Guide

### Step 1: Navigate to AcademicTorrents.com

1. Open a web browser and go to
   [AcademicTorrents.com](https://academictorrents.com).

2. In the search bar, type "Reddit" and press Enter. This will list available
   Reddit datasets, including monthly exports and the full dataset.

### Step 2: Find the Reddit Dataset

1. Look for the dataset titled something similar to **Reddit Data JSONL** or
   **Complete Reddit Dataset**. This dataset typically contains Reddit posts and
   comments in JSONL format, organized by year or month.

2. Click on the dataset name to view details, including the dataset description,
   size, and download options.

### Step 3: Download the .torrent File or Use the Magnet Link

1. On the dataset page, you’ll see options to either **Download .torrent** or **Copy Magnet Link**.
   - If using the **Download .torrent** option, save the `.torrent` file to your computer.
   - If using the **Magnet Link**, copy it to your clipboard (right-click and select “Copy link address”).

### Step 4: Start the Download with aria2c

1. Open a terminal on your Linux machine.
2. Use one of the following commands depending on whether you downloaded a `.torrent` file or copied the magnet link.

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

### Step 5: Verify and Access the Data

1. After the download is complete, navigate to the folder where you saved the
   dataset.

2. The files should be in **JSONL** format, where each line in a file is a JSON
   object representing a Reddit post or comment.

### Step 6: Organize or Process the Data (Optional)

You may want to organize the files by year or month if they aren’t already
organized this way. For efficient processing, you can use tools like `jq` or
write Python scripts to filter or extract specific fields.

### Step 7: Backup the Data (Optional)

Consider backing up the downloaded files to an external drive or cloud storage
given the dataset’s size.

## Example: Loading JSONL Data in Python

Once downloaded, you can load the JSONL files for analysis in Python as follows:

```python
import json

# Replace 'path/to/reddit_data.jsonl' with the actual path to your JSONL file
with open('path/to/reddit_data.jsonl', 'r') as file:
    for line in file:
        post = json.loads(line)
        print(post)  # Each 'post' is a dictionary representing a Reddit post/comment
```

## Tips and Notes

- **Monitor Disk Space**: Reddit datasets are large, and you may need to free up
    space as needed.

- **Check File Integrity**: aria2c will automatically verify the integrity of
    downloaded files.

- **JSONL Format**: JSONL (JSON Lines) format is efficient for large datasets
    but requires line-by-line processing, as shown in the example code above.

Following these steps will allow you to download and work with Reddit data from
AcademicTorrents.com efficiently.

## Setup and Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:gfariello/reddit-nature-climate-2024.git
   cd reddit-nature-climate-2024
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

## Usage

Run the main analysis script to collect data, perform text analysis, and
generate visualizations:

```bash
python main.py --subreddit climate --start-date 2005-01-01 --end-date 2021-06-30
```

### Available Arguments
- `--subreddit`: Subreddit to scrape (e.g., `climate`, `environment`).
- `--start-date`: Start date for data collection (YYYY-MM-DD).
- `--end-date`: End date for data collection (YYYY-MM-DD).

### Example
```bash
python main.py --subreddit climate --start-date 2020-01-01 --end-date 2020-12-31
```

## Data

Our analysis leverages data from:

- **Pushshift.io**: A comprehensive Reddit dataset, including posts and comments
    from 2005 through 2021.

- **Google Trends**: Historical search trends for "climate change" and "global
    warming," providing a secondary perspective on public interest.

Processed and supplementary data are available on FigShare for extended analysis:

- **[Data Repository on
    FigShare](http://dx.doi.org/10.6084/m9.figshare.26828467)**: Includes all
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
