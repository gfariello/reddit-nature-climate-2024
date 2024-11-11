#!/usr/bin/bash

# Load helper functions from general.sh
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source "${SCRIPT_DIR}/sh.lib/general.sh" || exit "Could not load required file: general.sh"

# Set default for threads to the number of cores available on the system
DEFAULT_THREADS=$(nproc)

# Function to display usage information
usage() {
    info "$(basename "$0") --input-dir dir --output-dir dir [--threads num]"
    info
    info "Recursively finds all JSONL files in the specified input directory and"
    info "runs Code/step-02-jsonl2csv on each file using a specified"
    info "number of threads. Results are saved in the specified output directory."
    info
    info "  --input-dir dir      The directory where JSONL files are located (required)."
    info "  --threads num        Number of threads to use. Defaults to ${DEFAULT_THREADS}."
    info "  --help or -h         Print this usage statement."
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --input-dir)
            input_dir="$2"
            shift; shift;
            ;;
        --threads)
            num_threads="$2"
            shift; shift;
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            fatal "Unknown option $1"
            ;;
    esac
done

# Check required arguments
if [ -z "${input_dir}" ]; then
    usage
    err "--input-dir is required."
    exit 1
fi

# Verify that input_dir contains 'Step-01-JSONL' directory
if [ ! -d "${input_dir}/Step-01-JSONL" ]; then
    usage
    fatal "No 'Step-01-JSONL' directory found in ${input_dir}."
fi

# Set number of threads to the default if not provided
if [ -z "${num_threads}" ]; then
    num_threads=${DEFAULT_THREADS}
fi

output_dir="${input_dir}/Step-02-Extracted-CSVs"
input_dir="${input_dir}/Step-01-JSONL"

# Create output directory if it doesn't exist
mkdir_if "${output_dir}"

# Find and count the matching files
matching_files=( $(find "${input_dir}" -type f -name 'R[CS]_20*.zst' | sort) )
file_count=${#matching_files[@]}

# Display the number of files found or show an error if no files are found
if [ "${file_count}" -eq 0 ]; then
    usage
    fatal "No files matching 'R[CS]_20*.zst' were found in ${input_dir}."
else
    info "Found ${file_count} files matching 'R[CS]_20*.zst' in ${input_dir}."
fi

# Set thread management parameters
set_max_threads "${num_threads}"
set_active_threads 0

# Process each JSONL file found in the input directory
process_files() {
    for file in "${matching_files[@]}"; do
        # Wait if maximum threads are active
        wait_if_max_threads

        # Log processing of the current file
        info "Processing ${file}..."

        mkdir_if "${output_dir}/logs"
        bname=$(basename "${file}")

        # Run the climate filter script in a subshell
        python3 "${SCRIPT_DIR}/step-02-jsonl2csv" -i "${file}" 2>&1 >> "${output_dir}/logs/${bname}.log" &

        # Don't launch too many at once.
        sleep 1.125

        # Increment active threads counter
        increment_threads
    done

    # Wait for all threads to complete
    wait_for_all_threads
    info "Completed processing all files."
}

# Run the file processing function
process_files
