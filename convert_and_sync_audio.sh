#!/bin/bash

# Audio Conversion and Sync Script
# Converts WMA files to MP3 and syncs to remote server
# Author: Claude Code Assistant
# Date: $(date +%Y-%m-%d)

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for rich console output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m' # No Color

# Default Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BASE_AUDIO_DIR="${SCRIPT_DIR}/app/static/audios"
readonly DEFAULT_TARGET="ET4"
readonly DEFAULT_REMOTE_HOST="maru"
readonly DEFAULT_REMOTE_PATH="/var/www/read-ai/shared/audios/"
readonly DEFAULT_MP3_BITRATE="192k"

# Script options (will be set by parse_args)
TARGET_DIR=""
REMOTE_HOST=""
REMOTE_PATH=""
MP3_BITRATE=""
ONLY_CONVERT=false
ONLY_SEND=false
ONLY_TRANSFER=false
SEND_FORMAT="all"

# Progress tracking
total_files=0
converted_files=0
skipped_files=0
failed_files=0

# Logging
readonly LOG_FILE="${SCRIPT_DIR}/audio_conversion_$(date +%Y%m%d_%H%M%S).log"

# Functions
show_help() {
    cat << EOF
${CYAN}Audio Conversion & Sync Tool${NC}
Converts WMA files to MP3 and syncs to remote server

${WHITE}USAGE:${NC}
    $(basename "$0") [OPTIONS]

${WHITE}OPTIONS:${NC}
    -s, --source DIR        Source directory relative to app/static/audios
                           (default: ${DEFAULT_TARGET})
    -r, --remote HOST       Remote host for sync (default: ${DEFAULT_REMOTE_HOST})
    -p, --path PATH         Remote path (default: ${DEFAULT_REMOTE_PATH})
    -b, --bitrate RATE      MP3 bitrate (default: ${DEFAULT_MP3_BITRATE})
    --only-convert          Only convert files, skip sync
    --only-send FORMAT      Only sync files, skip conversion
                           FORMAT: mp3|wma|all (default: all)
    --only-transfer         Only transfer files, skip conversion (alias for --only-send all)
    -h, --help             Show this help message
    -v, --verbose          Enable verbose logging

${WHITE}EXAMPLES:${NC}
    $(basename "$0") -s ET4
    $(basename "$0") -s audios/ET5 --only-convert
    $(basename "$0") -s ET4 --only-send mp3
    $(basename "$0") -s ET4/disc2 --only-transfer
    $(basename "$0") -s custom/folder -r myserver -p /data/audio/

${WHITE}SOURCE DIRECTORY:${NC}
    The source directory is relative to: ${BASE_AUDIO_DIR}
    Example: -s ET4 will use ${BASE_AUDIO_DIR}/ET4
             -s audios/ET4 will use ${BASE_AUDIO_DIR}/audios/ET4

EOF
}

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

parse_args() {
    # Set defaults
    TARGET_DIR="$DEFAULT_TARGET"
    REMOTE_HOST="$DEFAULT_REMOTE_HOST"
    REMOTE_PATH="$DEFAULT_REMOTE_PATH"
    MP3_BITRATE="$DEFAULT_MP3_BITRATE"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--source)
                TARGET_DIR="$2"
                shift 2
                ;;
            -r|--remote)
                REMOTE_HOST="$2"
                shift 2
                ;;
            -p|--path)
                REMOTE_PATH="$2"
                shift 2
                ;;
            -b|--bitrate)
                MP3_BITRATE="$2"
                shift 2
                ;;
            --only-convert)
                ONLY_CONVERT=true
                shift
                ;;
            --only-send)
                ONLY_SEND=true
                if [[ $# -gt 1 && ! $2 =~ ^- ]]; then
                    SEND_FORMAT="$2"
                    shift
                fi
                shift
                ;;
            --only-transfer)
                ONLY_TRANSFER=true
                ONLY_SEND=true
                SEND_FORMAT="all"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Validate arguments
    if [[ -z "$TARGET_DIR" ]]; then
        print_error "Source directory cannot be empty"
        exit 1
    fi
    
    # Validate send format
    if [[ "$SEND_FORMAT" != "mp3" && "$SEND_FORMAT" != "wma" && "$SEND_FORMAT" != "all" ]]; then
        print_error "Invalid send format: $SEND_FORMAT. Must be 'mp3', 'wma', or 'all'"
        exit 1
    fi
    
    # Validate conflicting options
    if [[ "$ONLY_CONVERT" == true && "$ONLY_SEND" == true ]]; then
        print_error "Cannot use both --only-convert and --only-send/--only-transfer"
        exit 1
    fi
}

print_header() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                          Audio Conversion & Sync Tool                       ║${NC}"
    echo -e "${CYAN}║                             WMA → MP3 Converter                              ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    local step_num=$1
    local step_desc=$2
    echo -e "${BLUE}▶ Step ${step_num}:${NC} ${WHITE}${step_desc}${NC}"
    echo "----------------------------------------"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${PURPLE}ℹ${NC} $1"
}

check_dependencies() {
    print_step 1 "Checking Dependencies"
    
    local missing_deps=()
    
    # Check for required commands
    for cmd in ffmpeg rsync ssh; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
            print_error "$cmd is not installed"
        else
            print_success "$cmd is available"
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_info "Please install the missing dependencies and try again"
        exit 1
    fi
    
    # Test remote host connectivity
    print_info "Testing remote host connectivity..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$REMOTE_HOST" echo "Connection test successful" 2>/dev/null; then
        print_success "Remote host '$REMOTE_HOST' is accessible"
    else
        print_error "Cannot connect to remote host '$REMOTE_HOST'"
        print_info "Please check your SSH configuration and network connectivity"
        exit 1
    fi
    
    echo ""
}

scan_files() {
    print_step 2 "Scanning Source Directory"
    
    local source_path="${BASE_AUDIO_DIR}/${TARGET_DIR}"
    
    if [ ! -d "$source_path" ]; then
        print_error "Source directory not found: $source_path"
        exit 1
    fi
    
    print_info "Scanning: $source_path"
    
    # Count WMA files
    local wma_count
    wma_count=$(find "$source_path" -name "*.wma" -type f | wc -l)
    
    # Count existing MP3 files
    local existing_mp3_count
    existing_mp3_count=$(find "$source_path" -name "*.mp3" -type f | wc -l)
    
    total_files=$wma_count
    
    print_success "Found $wma_count WMA files to convert"
    print_success "Found $existing_mp3_count existing MP3 files"
    
    if [ "$wma_count" -eq 0 ] && [ "$ONLY_SEND" == false ]; then
        print_warning "No WMA files found to convert"
        if [ "$existing_mp3_count" -eq 0 ]; then
            print_error "No audio files found in directory"
            return 1
        fi
        return 1
    fi
    
    echo ""
    return 0
}

convert_files() {
    print_step 3 "Converting WMA to MP3"
    
    local source_path="${BASE_AUDIO_DIR}/${TARGET_DIR}"
    local start_time=$(date +%s)
    
    print_info "Starting conversion with bitrate: $MP3_BITRATE"
    print_info "Conversion log: $LOG_FILE"
    echo ""
    
    # Create progress bar function
    show_progress() {
        local current=$1
        local total=$2
        local percent=$((current * 100 / total))
        local bar_length=50
        local filled_length=$((percent * bar_length / 100))
        
        printf "\r${CYAN}Progress: [${NC}"
        for ((i=0; i<filled_length; i++)); do printf "█"; done
        for ((i=filled_length; i<bar_length; i++)); do printf "░"; done
        printf "${CYAN}] %3d%% (%d/%d)${NC}" "$percent" "$current" "$total"
    }
    
    local file_count=0
    
    while IFS= read -r -d '' wma_file; do
        ((file_count++))
        
        local mp3_file="${wma_file%.wma}.mp3"
        local relative_path="${wma_file#$source_path/}"
        
        show_progress "$file_count" "$total_files"
        
        if [ -f "$mp3_file" ]; then
            ((skipped_files++))
            log "SKIP: $relative_path (MP3 already exists)"
            continue
        fi
        
        # Convert using ffmpeg with error handling
        if ffmpeg -i "$wma_file" -acodec mp3 -ab "$MP3_BITRATE" "$mp3_file" -y \
           -loglevel error -hide_banner 2>>"$LOG_FILE"; then
            ((converted_files++))
            log "CONVERT: $relative_path → ${relative_path%.wma}.mp3"
        else
            ((failed_files++))
            print_error "\nConversion failed for: $relative_path"
            log "ERROR: Failed to convert $relative_path"
        fi
        
    done < <(find "$source_path" -name "*.wma" -type f -print0)
    
    echo ""  # New line after progress bar
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    print_success "Conversion completed in ${duration}s"
    print_info "Converted: $converted_files files"
    print_info "Skipped: $skipped_files files (already exist)"
    
    if [ "$failed_files" -gt 0 ]; then
        print_warning "Failed: $failed_files files"
    fi
    
    echo ""
}

sync_to_remote() {
    print_step 4 "Syncing to Remote Server"
    
    local source_path="${BASE_AUDIO_DIR}/${TARGET_DIR}/"
    
    # Preserve directory structure - use TARGET_DIR as-is
    local remote_full_path="${REMOTE_HOST}:${REMOTE_PATH}${TARGET_DIR}/"
    
    print_info "Source: $source_path"
    print_info "Target: $remote_full_path"
    print_info "Send format: $SEND_FORMAT"
    echo ""
    
    print_info "Starting rsync transfer..."
    
    # Build rsync exclude/include options based on send format
    local rsync_opts=(-avz --progress --stats --human-readable)
    
    case "$SEND_FORMAT" in
        "mp3")
            rsync_opts+=(--include="*/" --include="*.mp3" --exclude="*")
            ;;
        "wma")
            rsync_opts+=(--include="*/" --include="*.wma" --exclude="*")
            ;;
        "all")
            # No additional filters, sync all files
            ;;
    esac
    
    # Rsync with progress and stats
    if rsync "${rsync_opts[@]}" "$source_path" "$remote_full_path" 2>&1 | \
       tee -a "$LOG_FILE"; then
        
        print_success "Remote sync completed successfully"
    else
        print_error "Remote sync failed"
        log "ERROR: rsync failed"
        exit 1
    fi
    
    echo ""
}

verify_sync() {
    print_step 5 "Verifying Remote Sync"
    
    print_info "Counting files on remote server..."
    
    # Preserve directory structure - use TARGET_DIR as-is
    local remote_dir="${REMOTE_PATH}${TARGET_DIR}"
    
    case "$SEND_FORMAT" in
        "mp3")
            local remote_count
            if remote_count=$(ssh "$REMOTE_HOST" \
                "find '$remote_dir' -name '*.mp3' -type f 2>/dev/null | wc -l" 2>/dev/null); then
                
                local local_count
                local_count=$(find "${BASE_AUDIO_DIR}/${TARGET_DIR}" -name "*.mp3" -type f | wc -l)
                
                print_info "Local MP3 files: $local_count"
                print_info "Remote MP3 files: $remote_count"
                
                if [ "$local_count" -eq "$remote_count" ]; then
                    print_success "MP3 file count verification passed"
                else
                    print_warning "MP3 file count mismatch detected"
                fi
            else
                print_warning "Could not verify remote MP3 file count"
            fi
            ;;
        "wma")
            local remote_count
            if remote_count=$(ssh "$REMOTE_HOST" \
                "find '$remote_dir' -name '*.wma' -type f 2>/dev/null | wc -l" 2>/dev/null); then
                
                local local_count
                local_count=$(find "${BASE_AUDIO_DIR}/${TARGET_DIR}" -name "*.wma" -type f | wc -l)
                
                print_info "Local WMA files: $local_count"
                print_info "Remote WMA files: $remote_count"
                
                if [ "$local_count" -eq "$remote_count" ]; then
                    print_success "WMA file count verification passed"
                else
                    print_warning "WMA file count mismatch detected"
                fi
            else
                print_warning "Could not verify remote WMA file count"
            fi
            ;;
        "all")
            local remote_mp3_count remote_wma_count
            if remote_mp3_count=$(ssh "$REMOTE_HOST" \
                "find '$remote_dir' -name '*.mp3' -type f 2>/dev/null | wc -l" 2>/dev/null) && \
               remote_wma_count=$(ssh "$REMOTE_HOST" \
                "find '$remote_dir' -name '*.wma' -type f 2>/dev/null | wc -l" 2>/dev/null); then
                
                local local_mp3_count local_wma_count
                local_mp3_count=$(find "${BASE_AUDIO_DIR}/${TARGET_DIR}" -name "*.mp3" -type f | wc -l)
                local_wma_count=$(find "${BASE_AUDIO_DIR}/${TARGET_DIR}" -name "*.wma" -type f | wc -l)
                
                print_info "Local files - MP3: $local_mp3_count, WMA: $local_wma_count"
                print_info "Remote files - MP3: $remote_mp3_count, WMA: $remote_wma_count"
                
                if [ "$local_mp3_count" -eq "$remote_mp3_count" ] && [ "$local_wma_count" -eq "$remote_wma_count" ]; then
                    print_success "File count verification passed"
                else
                    print_warning "File count mismatch detected"
                fi
            else
                print_warning "Could not verify remote file count"
            fi
            ;;
    esac
    
    echo ""
}

print_summary() {
    local end_time=$(date +%s)
    local total_duration=$((end_time - script_start_time))
    
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                               SUMMARY REPORT                                 ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    print_info "Total execution time: ${total_duration}s"
    print_info "Source directory: ${BASE_AUDIO_DIR}/${TARGET_DIR}"
    
    # Preserve directory structure - use TARGET_DIR as-is
    print_info "Remote destination: ${REMOTE_HOST}:${REMOTE_PATH}${TARGET_DIR}/"
    
    # Show operation mode
    if [ "$ONLY_CONVERT" == true ]; then
        print_info "Operation mode: Convert only"
    elif [ "$ONLY_TRANSFER" == true ]; then
        print_info "Operation mode: Transfer only (all files)"
    elif [ "$ONLY_SEND" == true ]; then
        print_info "Operation mode: Send only ($SEND_FORMAT files)"
    else
        print_info "Operation mode: Convert and sync"
    fi
    
    echo ""
    
    if [ "$ONLY_SEND" == false ]; then
        echo -e "${WHITE}Conversion Results:${NC}"
        print_success "Files converted: $converted_files"
        print_info "Files skipped: $skipped_files"
        
        if [ "$failed_files" -gt 0 ]; then
            print_warning "Files failed: $failed_files"
        fi
        echo ""
    fi
    
    print_info "Detailed log saved to: $LOG_FILE"
    echo ""
    
    if [ "$failed_files" -eq 0 ]; then
        print_success "🎉 All operations completed successfully!"
    else
        print_warning "⚠️  Operation completed with some warnings. Check the log file for details."
    fi
    
    echo ""
}

cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Script interrupted or failed"
        log "SCRIPT: Interrupted or failed"
    fi
}

# Main execution
main() {
    local script_start_time=$(date +%s)
    
    # Parse command line arguments first
    parse_args "$@"
    
    # Set up error handling
    trap cleanup EXIT
    
    # Initialize log
    log "SCRIPT: Starting audio conversion and sync process"
    log "SCRIPT: Source directory - ${BASE_AUDIO_DIR}/${TARGET_DIR}"
    # Preserve directory structure - use TARGET_DIR as-is
    log "SCRIPT: Remote destination - ${REMOTE_HOST}:${REMOTE_PATH}${TARGET_DIR}/"
    log "SCRIPT: Operation mode - Convert: $([ "$ONLY_SEND" == false ] && echo "Yes" || echo "No"), Send: $([ "$ONLY_CONVERT" == false ] && echo "Yes ($SEND_FORMAT)" || echo "No")"
    
    print_header
    
    # Show current configuration
    print_info "Configuration:"
    print_info "  Source: ${BASE_AUDIO_DIR}/${TARGET_DIR}"
    # Preserve directory structure - use TARGET_DIR as-is
    print_info "  Remote: ${REMOTE_HOST}:${REMOTE_PATH}${TARGET_DIR}/"
    print_info "  Bitrate: ${MP3_BITRATE}"
    if [ "$ONLY_CONVERT" == true ]; then
        print_info "  Mode: Convert only"
    elif [ "$ONLY_TRANSFER" == true ]; then
        print_info "  Mode: Transfer only (all files)"
    elif [ "$ONLY_SEND" == true ]; then
        print_info "  Mode: Send only ($SEND_FORMAT files)"
    else
        print_info "  Mode: Convert and sync"
    fi
    echo ""
    
    # Execute steps based on mode
    if [ "$ONLY_SEND" == true ]; then
        # Only sync mode
        check_dependencies
        scan_files  # Still scan to show file counts
        sync_to_remote
        verify_sync
    elif [ "$ONLY_CONVERT" == true ]; then
        # Only convert mode
        if scan_files; then
            convert_files
        else
            print_info "No WMA files found to convert"
        fi
    else
        # Full mode: convert and sync
        check_dependencies
        
        if scan_files; then
            convert_files
            sync_to_remote
            verify_sync
        else
            print_info "Skipping conversion step - no WMA files found"
            print_info "Proceeding with sync of existing files..."
            sync_to_remote
            verify_sync
        fi
    fi
    
    print_summary
    
    log "SCRIPT: Process completed successfully"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi