_gen_red=`tput setaf 1`
_gen_gre=`tput setaf 2`
_gen_yel=`tput setaf 3`
_gen_blu=`tput setaf 4`
_gen_mag=`tput setaf 5`
_gen_cya=`tput setaf 6`
_gen_wit=`tput setaf 7`
_gen_non=`tput sgr0`
_gen_cwd=`realpath .`
_gen_cwd_base=`basename "${cwd}"`
_gen_t0=`date "+%s.%N"`
_gen_t02=`date "+%s"`

debug_on() { _gen_debug="TRUE"; }
debug_off() { _gen_debug=""; }

get_secs() {
    echo "$(date +%s.%N)-${_gen_t0}" | bc
}

get_time() {
    date -d@`echo "$(date +%s)-${_gen_t02}" | bc` -u +%H:%M:%S
}

warn()  { for line in "$@"; do echo "[$(get_time) ${_gen_yel}WARN${_gen_non} ] $line"; done; }
info()  { for line in "$@"; do echo "[$(get_time) ${_gen_gre}INFO${_gen_non} ] $line"; done; }
fatal() { for line in "$@"; do echo "[$(get_time) ${_gen_red}FATAL${_gen_non}] $line"; done; exit 1; }
h1_line () { info "=============================================================================="; }
h2_line () { info "------------------------------------------------------------------------------"; }
h1()       { h1_line; info "$@"; h1_line; }
h2()       { h2_line; info "$@"; h2_line; }
err()   {
    for line in "$@"
    do
        echo "[${_gen_red}ERROR${_gen_non}]: $line"
        if [ -z "${error_count}" ]; then
            error_count=0
        fi
        error_count=$((error_count+1))
    done
}
debug() {
    if [ -n "${_gen_debug}" ]; then
        for line in "$@"
        do
            echo "[${_gen_cya}DEBUG${_gen_non}]: $line"
        done
    fi
}


current_secs() {
    _gen_t1=$(date "+%s.%N")
    export _gen_secs=$(echo "$_gen_t1-$_gen_t0" | bc)
    # echo "$_gen_secs seconds"
}

exit_errors() {
    if [ -n "${error_count}" ]; then
        _gen_t1=$(date "+%s.%N")
        _gen_secs=$(echo "$_gen_t1-$_gen_t0" | bc)
        err "${error_count} Errors encountered, cannot continue. Exiting after $_gen_secs seconds"
        exit 1
    fi
}

check_cwd() {
    if [[ "${1}" != "${_gen_cwd_base}" ]]; then
        warn "This was not run from the expected '${1}' directory."
    fi
}

require_cwd() {
    if [[ "${1}" != "${_gen_cwd_base}" ]]; then
        fatal "This was not run from the expected '${p}' directory."
    fi
}

mkdirif() {
    if [ ! -e "${1}" ]; then
        info "Creating directory ${1}"
        mkdir -p "${1}" || exit 1
    fi
}

mkdir_if() {
    if [ ! -e "${1}" ]; then
        info "Creating directory ${1}"
        mkdir -p "${1}" || exit 1
    fi
}

must_cd() {
    info "Changing directory to '$1'"
    cd $1 || fatal "Failed to change directory to '$1': Exited $?"
}

com_or_sub() {
    if [[ ! -z "$2" ]]; then
        fatal "Usate: "`basename "$0"`" (Comments|Submissions)"
    fi
    if [[ "$1" == "Comments" ]]; then
        h=`hostname`
        if [[ ! "$h" == *"u"[0-9][0-9] ]]; then
            fatal "Comments work needs to be run on the secondary nodes."
        fi
        in_dir="/mnt/k/Data/Reddit/Orig/Submissions/csvs.sorted"
        out_dir="/mnt/d/Data/Reddit/Orig/Submissions/csvs.sorted.merged"
    elif [[ "$1" == "Submissions" ]]; then
        h=`hostname`
        if [[ ! "$h" == *"BL"[0-9][0-9] ]]; then
            fatal "Submissions work needs to be run on the primary nodes."
        fi
        pass_01_csv_dir="/mnt/k/Data/Reddit/Orig/Submissions/csvs"
        pass_02_csv_dir="/mnt/k/Data/Reddit/Orig/Submissions/csvs.sorted"
        pass_03_csv_dir="/mnt/d/Data/Reddit/Orig/Submissions"
        pass_04_csv_dir="/mnt/k/Data/Reddit/Orig/Submissions/csvs.sorted.merged.uniq"
        pass_05_csv_dir="/mnt/k/Data/Reddit/Orig/Submissions/csvs.cleaned"
        pass_06_csv_dir="/mnt/k/Data/Reddit/Orig/Submissions/csvs.cleaned.lang"
        pass_07_csv_dir="/mnt/k/Data/Reddit/Orig/Submissions/csvs.cleaned.sentiment"
    else
        fatal "Usate: "`basename "$0"`" (Comments|Submissions)"
    fi
    pass_01_meta_dir="${pass_01_csv_dir}/meta"
    pass_01_ids_dir="${pass_01_meta_dir}/ids"
    pass_01_md5_dir="${pass_01_meta_dir}/md5"
    pass_01_count_dir="${pass_01_meta_dir}/count"
    pass_0_meta_dir="${pass_01_csv_dir}/meta"
    pass_0_ids_dir="${pass_01_meta_dir}/ids"
    pass_0_md5_dir="${pass_01_meta_dir}/md5"
    pass_0_count_dir="${pass_01_meta_dir}/count"
}

_general_active_threads=0
_general_max_threads=12
_gemeral_log_dir="logs"

set_active_threads () {
    info "Setting active threads to '${1}'."
    _general_active_threads="$1"
}

set_max_threads () {
    info "Setting max threads to '${1}'."
    _general_max_threads="$1"
}

decrement_threads () {
    _general_active_threads=$(("${_general_active_threads}" - 1))
    debug "decrement_threads: _general_active_threads=${_general_active_threads}"
}

increment_threads () {
    _general_active_threads=$(("${_general_active_threads}" + 1))
    debug "increment_threads: _general_active_threads=${_general_active_threads}"
}

wait_if_max_threads () {
    debug "wait_if_max_threads: _general_active_threads=${_general_active_threads}, _general_max_threads=${_general_max_threads}"
    # While there ${_general_max_threads} or more threads
    while [ "${_general_active_threads}" -ge "${_general_max_threads}" ]
    do
        debug "$(ps --ppid $$ -o pid,cmd | cut -c 1-120 | grep -v ' ps ')"
        num_children="$(ps --ppid $$ --no-headers | grep -v ' ps ' | wc -l)"
        debug "Num children: $num_children"
        # Wait for one process to finish
        info "There are ${_general_active_threads}/${_general_max_threads} threads active. Waiting for processes to finish."
        if wait -n; then
            # One thread finished and exited 0, so we decrement the count and continue.
            debug "Last process returned $?"
            decrement_threads
        else
            debug "Last process returned $? - ERROR"
            # The last thread exited non-zero. We don't continue on errors
            err "Check ${_gemeral_log_dir}/*.log files"
            # Wait 10 seconds so that some of the logs get flushed
            sleep 10
            # Try to see which logs don't have 'FINISHED' in them
            grep -L FINISHED "${_gemeral_log_dir}/"*.log
            # Exit the script with an error.
            fatal "Last process exited abnormally, terminating"
        fi
    done
}

wait_for_all_threads () {
    debug "wait_for_all_threads: _general_active_threads=${_general_active_threads}, _general_max_threads=${_general_max_threads}"
    # While there ${_general_max_threads} or more threads
    debug "$(ps --ppid $$ -o pid,cmd | cut -c 1-120 | grep -v ' ps ')"
    num_children="$(ps --ppid $$ --no-headers | grep -v ' ps ' | wc -l)"
    debug "Num children: $num_children"
    # Wait for all processes to finish
    info "There are ${_general_active_threads}/${_general_max_threads} threads active. Waiting all for processes to finish."
    if wait; then
        # One thread finished and exited 0, so we decrement the count and continue.
        debug "All threads returned $?"
        set_active_threads 0
    else
        debug "Wait returned $? - ERROR"
        # The last thread exited non-zero. We don't continue on errors
        err "Check ${_gemeral_log_dir}/*.log files"
        # Wait 10 seconds so that some of the logs get flushed
        sleep 10
        # Try to see which logs don't have 'FINISHED' in them
        grep -L FINISHED "${_gemeral_log_dir}/"*.log
        # Exit the script with an error.
        fatal "One or more child processes exited abnormally, terminating"
    fi
}

# Compare version numbers. Taken (possibly modified) from
# https://stackoverflow.com/questions/4023830.
# Returns 0 if =, 1 if >, 2 if if <
_vercomp () {
    if [[ $1 == $2 ]]
    then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    # fill empty fields in ver1 with zeros
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++))
    do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++))
    do
        if [[ -z ${ver2[i]} ]]
        then
            # fill empty fields in ver2 with zeros
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]}))
        then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]}))
        then
            return 2
        fi
    done
    return 0
}

# Check that version requirements are met. Examples:
#     vercomp "1.1" ">=" "1"   # returns 0 (true).
#     vercomp "1.1" ">=" "1.0" # returns 0 (true).
#     vercomp "1" ">" "1.0"    # returns 1 (false).
# Etc.
vercomp() {
    version="$1"
    direction="$2"
    reference="$3"
    _vercomp "$reference" "$version"
    result="$?"
    if [ "$result" = "0" ]; then
        case "$direction" in
            "="|">="|"<=")
                return 1
                ;;
            *)
                return 0
                ;;
        esac
    fi
    if [ "$result" = "1" ]; then
        case "$direction" in
            ">"|">=")
                return 1
                ;;
            *)
                return 0
                ;;
        esac
    fi
    if [ "$result" = "2" ]; then
        case "$direction" in
            "<"|"<=")
                return 1
                ;;
            *)
                return 0
                ;;
        esac
    fi
}

check_python_version() {
    pversion=$(python3 -V 2>&1 | grep -Po '(?<=Python )(.+)')
    if vercomp "$pversion" "<" "3.8"; then
        fatal "python3 returned version '$pversion', but we need a version >= 3.8.0, sorry."
    fi
}
