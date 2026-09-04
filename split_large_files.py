import os

CHUNK_SIZE = 1500 * 1024 * 1024  # 1.5 GB in bytes

FILES_TO_SPLIT = [
    {
        "file": "RSMC_hycom_20260904.nc",
        "output_dir": "hycom"
    },
    {
        "file": "rsmc_combined_ww3_20260903.nc",
        "output_dir": "combined"
    }
]

def split_file(item):
    filename = item["file"]
    output_dir = item["output_dir"]
    
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    file_size = os.path.getsize(filename)
    print(f"\n--- Splitting {filename} ({file_size / (1024**3):.2f} GB) into '{output_dir}/' ---")
    
    part_num = 1
    bytes_read_total = 0
    
    with open(filename, 'rb') as f_in:
        while True:
            part_filename = os.path.join(output_dir, f"{filename}.part{part_num}")
            if os.path.exists(part_filename) and os.path.getsize(part_filename) > 0:
                print(f"Part already exists: {part_filename} ({os.path.getsize(part_filename)/(1024**3):.2f} GB)")
                f_in.seek(CHUNK_SIZE, os.SEEK_CUR)
                bytes_read_total += CHUNK_SIZE
                part_num += 1
                if bytes_read_total >= file_size:
                    break
                continue
                
            print(f"Writing {part_filename}...")
            with open(part_filename, 'wb') as f_out:
                bytes_written = 0
                while bytes_written < CHUNK_SIZE:
                    read_block = min(64 * 1024 * 1024, CHUNK_SIZE - bytes_written)
                    chunk = f_in.read(read_block)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    bytes_written += len(chunk)
                    bytes_read_total += len(chunk)
            
            print(f"Completed {part_filename} ({os.path.getsize(part_filename) / (1024**2):.2f} MB)")
            part_num += 1
            if bytes_read_total >= file_size:
                break
                
    print(f"Successfully split {filename} into {part_num - 1} parts in '{output_dir}/'.")

if __name__ == "__main__":
    for item in FILES_TO_SPLIT:
        split_file(item)
